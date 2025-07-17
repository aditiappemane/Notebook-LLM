import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import os
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key=" + GEMINI_API_KEY

# Initialize Chroma client and collection
chroma_client = chromadb.Client(Settings(persist_directory="chroma_data"))
collection = chroma_client.get_or_create_collection(
    name="notebook_llm_docs",
    metadata={"hnsw:space": "cosine"}
)

# Embedding function using Gemini

def embed_text(texts):
    vectors = []
    for text in texts:
        payload = {
            "model": "models/embedding-001",
            "content": {"parts": [{"text": text}]}
        }
        response = requests.post(GEMINI_EMBED_URL, json=payload)
        if response.status_code == 200:
            data = response.json()
            embedding = data["embedding"]["values"]
            vectors.append(embedding)
        else:
            raise Exception(f"Gemini embedding error: {response.text}")
    return vectors


def add_chunks_to_chroma(chunks, metadatas, ids):
    vectors = embed_text(chunks)
    collection.add(
        documents=chunks,
        embeddings=vectors,
        metadatas=metadatas,
        ids=ids
    )


def query_chroma(query, n_results=5, metadata_filter=None):
    query_vector = embed_text([query])[0]
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        where=metadata_filter
    )
    return results 