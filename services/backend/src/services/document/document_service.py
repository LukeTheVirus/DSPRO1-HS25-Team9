import hashlib
import uuid
import os
import json
from typing import List, Dict, Any

from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct, MatchAny, Range, ScoredPoint

from .document_data import DocumentData
from .document_result import DocumentResult
from ..external.embedding_service import EmbeddingService
from ..external.qdrant_service import QdrantService, DOCUMENTS_COLLECTION, DOCUMENT_IDENTIFIER_FIELD
from ..external.unstructured_service import UnstructuredService


class DocumentService:
    def __init__(self, qdrant_service: QdrantService, embedding_service: EmbeddingService,
                 unstructured_service: UnstructuredService):
        self._qdrant_service = qdrant_service
        self._embedding_service = embedding_service
        self._unstructured_service = unstructured_service

    async def insert_document(self, identifier: str, raw_content: bytes, content_type: str = "text/plain"):
        document_hash = hashlib.sha256(raw_content).hexdigest()
        qdrant = await self._qdrant_service.get_client()
        query_result = await qdrant.query_points(
            collection_name=DOCUMENTS_COLLECTION,
            query_filter=Filter(must=[FieldCondition(key="hash", match=MatchValue(value=document_hash))]),
            limit=1
        )
        if len(query_result.points) > 0:
            return False
        
        filename = os.path.basename(identifier)
        parsed_document = await self._unstructured_service.parse_document(filename, content_type, raw_content)
        chunks = parsed_document.get("chunks", [])
        embeddings = await self._embedding_service.embed_texts([chunk["text"] for chunk in chunks])

        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)): 
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "identifier": identifier,
                        "hash": document_hash,
                        "chunk_sequence": i,
                        "text_content": chunk["text"],
                    }
                )
            )
        await qdrant.upsert(collection_name=DOCUMENTS_COLLECTION, points=points)
        return True

    async def retrieve_and_enrich_context(self, 
                                            query_vector: List[float], 
                                            neighbor_count: int, 
                                            score_threshold: float, 
                                            top_k_docs: int,
                                            retrieval_limit: int = 20) -> Dict[str, Any]:
        
        qdrant = await self._qdrant_service.get_client()

        # Step 1 & 2: Get all chunks > threshold
        search_results = await qdrant.search(
            collection_name=DOCUMENTS_COLLECTION,
            query_vector=query_vector,
            limit=retrieval_limit,
            with_payload=True,
            score_threshold=score_threshold
        )

        # Step 3: Group by doc_id
        doc_groups = {}
        for point in search_results:
            doc_id = point.payload.get(DOCUMENT_IDENTIFIER_FIELD)
            if doc_id:
                if doc_id not in doc_groups:
                    doc_groups[doc_id] = []
                doc_groups[doc_id].append(point)
        
        # Step 4: Sort groups by best score and keep top_k
        sorted_groups = sorted(doc_groups.items(), key=lambda item: item[1][0].score, reverse=True)
        top_groups = dict(sorted_groups[:top_k_docs])
        
        # Store the best score for each of the top docs
        doc_best_scores = {doc_id: points[0].score for doc_id, points in top_groups.items()}

        if not top_groups:
            return {}

        # Step 5: Find all sequence numbers to fetch (relevant chunks + neighbors)
        fetch_requests = {}
        for doc_id, points in top_groups.items():
            sequences_to_fetch = set()
            for point in points: # For ALL relevant chunks
                seq = point.payload.get("chunk_sequence", -1)
                if seq != -1:
                    for i in range(max(0, seq - neighbor_count), seq + neighbor_count + 1):
                        sequences_to_fetch.add(i)
            fetch_requests[doc_id] = sorted(list(sequences_to_fetch))

        # Step 6: Retrieve all chunks
        all_context_points = []
        for doc_id, sequences in fetch_requests.items():
            if not sequences:
                continue
            
            min_seq, max_seq = min(sequences), max(sequences)
            
            neighbor_filter = Filter(
                must=[
                    FieldCondition(key=DOCUMENT_IDENTIFIER_FIELD, match=MatchValue(value=doc_id)),
                    FieldCondition(key="chunk_sequence", range=Range(gte=min_seq, lte=max_seq))
                ]
            )

            retrieved_data, _ = await qdrant.scroll(
                collection_name=DOCUMENTS_COLLECTION,
                scroll_filter=neighbor_filter, 
                with_payload=True, with_vectors=False, limit=50
            )
            
            for point in retrieved_data:
                if point.payload.get("chunk_sequence") in sequences:
                    all_context_points.append(point)

        # Step 7: Process and format
        documents_map = {}
        for point in all_context_points:
            doc_id = point.payload.get(DOCUMENT_IDENTIFIER_FIELD)
            sequence = point.payload.get("chunk_sequence", -1) 
            text = point.payload.get("text_content")
            
            if doc_id and text:
                if doc_id not in documents_map:
                    documents_map[doc_id] = {}
                documents_map[doc_id][sequence] = text

        # Build the final context object with all the metadata
        context_obj = {}
        for doc_id, chunk_dict in documents_map.items():
            # Ensure we only return docs that were in the top_k
            if doc_id in top_groups:
                sorted_sequences = sorted(chunk_dict.keys())
                full_doc_text = "\n".join(chunk_dict[s] for s in sorted_sequences)
                
                context_obj[doc_id] = {
                    "text_content": full_doc_text,
                    "best_score": doc_best_scores[doc_id],
                    "retrieved_chunks": len(chunk_dict)
                }
            
        return context_obj
    
    async def search(self, query: str, limit: int = 5) -> List[DocumentResult]:
        query_embedding = (await self._embedding_service.embed_texts([query]))[0]
        qdrant = await self._qdrant_service.get_client()
        query_result = await qdrant.query_points(DOCUMENTS_COLLECTION, query_embedding, limit=limit)
        hits = []
        for point in query_result.points:
            identifier = point.payload.get("identifier")
            text_content = point.payload.get("text_content")
            hash = point.payload.get("hash")
            document_result = DocumentResult(DocumentData(identifier, hash, text_content), point.score)
            hits.append(document_result)
        return hits

    async def delete_by_identifier(self, identifier: str):
        qdrant = await self._qdrant_service.get_client()
        await qdrant.delete(
            collection_name=DOCUMENTS_COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="identifier",
                        match=MatchValue(value=identifier)
                    )
                ]
            )
        )