import chromadb
import os
from sentence_transformers import SentenceTransformer

_model = None
_collection = None

def get_model():
    """Load embedding model once and reuse."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def get_collection():
    """Connect to ChromaDB collection."""
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path="chroma_db")
        _collection = client.get_collection("defects")
    return _collection

def find_similar(query, n_results=3):
    """
    Find the most similar chunks to a query string.
    Returns list of dicts with text, filename, and chunk index.
    """
    model = get_model()
    collection = get_collection()

    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )

    similar = []
    for doc, meta in zip(results["documents"][0],
                          results["metadatas"][0]):
        similar.append({
            "text": doc,
            "filename": meta["filename"],
            "chunk_index": meta["chunk_index"],
            "source_type": meta["source_type"]
        })
    return similar

def build_context(query, n_results=3):
    """
    Build a context string from similar chunks for RAG prompting.
    """
    similar = find_similar(query, n_results)
    context_parts = []
    for i, s in enumerate(similar, 1):
        context_parts.append(
            f"[Similar case {i} from {s['filename']}]\n{s['text'][:500]}"
        )
    return "\n\n".join(context_parts)
