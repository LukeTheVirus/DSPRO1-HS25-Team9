from ...container import Container
from ...services.external.embedding_service import EmbeddingService
from ...services.external.qdrant_service import QdrantService
from ...services.external.ollama_service import OllamaService

# Import constants from the Qdrant service
from ...services.external.qdrant_service import DOCUMENTS_COLLECTION, DOCUMENT_IDENTIFIER_FIELD

# --- Workflow Configuration ---
OLLAMA_MODEL = "llama3:8b"
# The prompt for the *first* LLM call to expand the query
QUERY_EXPANSION_PROMPT_TEMPLATE = """
You are an expert search assistant. Given the user's question, generate a short, hypothetical
passage that would be a perfect answer. This passage will be used for a semantic search.
Do not answer the question; just generate the hypothetical answer text.

USER QUESTION:
{user_input}

HYPOTHETICAL ANSWER:
"""

# The prompt for the *second* LLM call to generate the final answer
FINAL_ANSWER_PROMPT_TEMPLATE = """
You are a helpful assistant. Answer the user's question based ONLY on the context provided.
If the context does not contain the answer, say "I do not have that information."

CONTEXT:
{context}

USER QUESTION:
{user_input}

ANSWER:
"""
# ------------------------------


async def default_workflow(container: Container, user_input: str, **kwargs) -> dict:
    """
    Executes the default RAG workflow with Query Expansion.
    Returns a dictionary containing the final answer and intermediate steps.
    """
    
    # 1. Resolve services
    embed_service = container.resolve(EmbeddingService)
    qdrant_service = container.resolve(QdrantService)
    ollama_service = container.resolve(OllamaService)

    await qdrant_service.initialize()
    qdrant_client = await qdrant_service.get_client()

    # --- Step 1: Query Expansion ---
    print(f"Expanding query: '{user_input}'")
    expansion_prompt = QUERY_EXPANSION_PROMPT_TEMPLATE.format(user_input=user_input)
    
    generated_search_query = await ollama_service.generate_response(
        model=OLLAMA_MODEL,
        prompt=expansion_prompt
    )
    # Clean up the generated query (e.g., remove quotes)
    generated_search_query = generated_search_query.strip().strip('\"')

    # 2. Embed the *new* search query
    print(f"Embedding generated query: '{generated_search_query}'")
    query_vector = (await embed_service.embed_texts([generated_search_query]))[0]

    # --- Step 2: Retrieve Top 5 Unique Documents ---
    print(f"Searching for 5 unique documents...")
    # Use search_groups to get the top hit from 5 unique groups
    search_groups_result = await qdrant_client.search_groups(
        collection_name=DOCUMENTS_COLLECTION,
        query_vector=query_vector,
        # Use the correct field from DocumentService
        group_by=DOCUMENT_IDENTIFIER_FIELD, 
        group_size=1, # Get 1 hit from each document
        limit=5,      # Get 5 unique documents
        with_payload=True 
    )

    # 3. Build context from the unique results
    context = ""
    if search_groups_result.groups:
        for group in search_groups_result.groups:
            hit = group.hits[0] 
            # Use the correct payload fields from DocumentService
            if 'text_content' in hit.payload:
                doc_id = hit.payload.get(DOCUMENT_IDENTIFIER_FIELD, 'unknown')
                context += f"--- Context from document: {doc_id} ---\n"
                context += f"{hit.payload['text_content']}\n\n"

    if not context:
        print("No context found.")
        context = "No information found."

    # --- Step 3: Generate Final Answer ---
    print("Generating final response with context...")
    final_prompt = FINAL_ANSWER_PROMPT_TEMPLATE.format(
        context=context,
        user_input=user_input
    )
    
    final_answer = await ollama_service.generate_response(
        model=OLLAMA_MODEL,
        prompt=final_prompt
    )
    
    # 4. Return the full log
    return {
        "final_answer": final_answer,
        "generated_search_query": generated_search_query,
        "retrieved_context": context
    }