import os
import chromadb
from chromadb.config import Settings
from typing import List
from dotenv import load_dotenv

load_dotenv()

_client = None
_collection = None

CHROMA_PERSIST_PATH = os.getenv("CHROMA_PERSIST_PATH", "./data/processed/chroma")
COLLECTION_NAME = "rag_chunks"


def get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
    return _client


def get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def store_chunks(chunks: List[dict]) -> int:
    if not chunks:
        raise ValueError("No chunks provided to store.")

    for chunk in chunks:
        if "embedding" not in chunk:
            raise ValueError(f"Chunk {chunk.get('chunk_id')} is missing embedding.")

    collection = get_collection()

    ids = [chunk["chunk_id"] for chunk in chunks]
    embeddings = [chunk["embedding"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [
        {
            "doc_id": chunk["doc_id"],
            "file_name": chunk["file_name"],
            "page_number": chunk["page_number"],
            "chunk_index": chunk["chunk_index"],
            "char_count": chunk["char_count"],
            "embedding_model": chunk.get("embedding_model", "unknown"),
        }
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    return len(chunks)


def search_chunks(query_embedding: List[float], top_k: int = 10, doc_id: str = None) -> List[dict]:
    if not query_embedding:
        raise ValueError("Query embedding cannot be empty.")

    collection = get_collection()

    where_filter = {"doc_id": doc_id} if doc_id else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append({
            "chunk_id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "similarity_score": round(1 - results["distances"][0][i], 4),
        })

    return chunks


def delete_document(doc_id: str) -> int:
    collection = get_collection()
    results = collection.get(where={"doc_id": doc_id})
    ids_to_delete = results["ids"]

    if ids_to_delete:
        collection.delete(ids=ids_to_delete)

    return len(ids_to_delete)


def get_document_count() -> int:
    collection = get_collection()
    return collection.count()