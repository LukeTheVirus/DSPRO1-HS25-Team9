import json
from ...container import Container
from ...services.external.embedding_service import EmbeddingService
from ...services.external.qdrant_service import QdrantService
from ...services.external.ollama_service import OllamaService
from ...services.document.document_service import DocumentService 

# --- Workflow Configuration ---
OLLAMA_MODEL = "llama3:8b"
NEIGHBOR_COUNT = 4
TOP_K_DOCS = 5
SCORE_THRESHOLD = 0.5
RETRIEVAL_LIMIT = 20

QUERY_EXPANSION_PROMPT_TEMPLATE = """
You are an expert search assistant. Your task is to generate a short, hypothetical
passage that would be a perfect, comprehensive answer to the user's question.
This passage will be used for a semantic search.
Do not write a conversational response, just generate the hypothetical answer text.

USER QUESTION:
{user_input}

HYPOTHETICAL ANSWER:
"""

# --- Updated Prompt to expect XML ---
FINAL_ANSWER_PROMPT_TEMPLATE = """
You are a helpful assistant. Answer the user's question based ONLY on the context provided.
The context will be provided inside <DOCUMENT> tags.
If the context does not contain the answer, say "I do not have that information."

CONTEXT:
{context}

USER QUESTION:
{user_input}

ANSWER:
"""
# ------------------------------


async def default_workflow(container: Container, user_input: str, **kwargs) -> dict:
    
    # 1. Resolve services
    embed_service = container.resolve(EmbeddingService)
    qdrant_service = container.resolve(QdrantService)
    ollama_service = container.resolve(OllamaService)
    document_service = container.resolve(DocumentService) 

    await qdrant_service.initialize()

    # --- Step 1: Query Expansion ---
    print(f"Expanding query: '{user_input}'")
    expansion_prompt = QUERY_EXPANSION_PROMPT_TEMPLATE.format(user_input=user_input)
    generated_search_query = await ollama_service.generate_response(
        model=OLLAMA_MODEL,
        prompt=expansion_prompt
    )
    generated_search_query = generated_search_query.strip().strip('\"')

    # --- Step 2: Embed the new search query ---
    print(f"Embedding generated query: '{generated_search_query}'")
    query_vector = (await embed_service.embed_texts([generated_search_query]))[0]

    # --- Step 3: Retrieve and Enrich Context ---
    print(f"Retrieving and enriching context...")
    context_obj = await document_service.retrieve_and_enrich_context(
        query_vector=query_vector,
        neighbor_count=NEIGHBOR_COUNT,
        score_threshold=SCORE_THRESHOLD,
        top_k_docs=TOP_K_DOCS,
        retrieval_limit=RETRIEVAL_LIMIT
    )

    # --- Step 4: Prepare context for LLM and API ---
    if not context_obj:
        print("No context found.")
        context_str = "No information found."
    else:
        # Build a clean XML-style string for the LLM
        context_parts = []
        for doc_id, data in context_obj.items():
            context_parts.append(f"<DOCUMENT id='{doc_id}'>")
            context_parts.append(data["text_content"])
            context_parts.append("</DOCUMENT>\n")
        context_str = "\n".join(context_parts)

    # --- Step 5: Generate Final Answer ---
    print("Generating final response with enriched context...")
    final_prompt = FINAL_ANSWER_PROMPT_TEMPLATE.format(
        context=context_str, # Pass the clean XML string
        user_input=user_input
    )
    final_answer = await ollama_service.generate_response(
        model=OLLAMA_MODEL,
        prompt=final_prompt
    )
    
    # --- Step 6: Return the full log ---
    return {
        "final_answer": final_answer,
        "generated_search_query": generated_search_query,
        "retrieved_context": context_obj # Pass the rich object to the API
    }