"""
Retriever over ChromaDB using OpenAI embeddings.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
import chromadb
from openai import OpenAI

EMBED_MODEL = "text-embedding-3-small"

# Structure for the retrieval results
@dataclass
class RAGResult:
    title: str
    score: float
    snippet: str

# Retriever class for querying ChromaDB
class Retriever:
    def __init__(self, persist_dir: str):
        self.client = OpenAI()
        self.db = chromadb.PersistentClient(path=persist_dir)
        self.coll = self.db.get_or_create_collection("book_summaries")

    def embed(self, text: str) -> List[float]:
        r = self.client.embeddings.create(model=EMBED_MODEL, input=[text])
        return r.data[0].embedding

    def search(self, query: str, top_k: int = 3) -> List[RAGResult]:
        q_emb = self.embed(query)
        res = self.coll.query(
            query_embeddings=[q_emb],
            n_results=top_k,
            include=["metadatas", "documents", "distances"]
        )
        results = []
        for i in range(len(res["ids"][0])):
            title = res["metadatas"][0][i]["title"]
            doc = res["documents"][0][i]
            dist = res["distances"][0][i]
            score = 1.0 / (1.0 + dist)  # convert distance to similarity-ish
            results.append(RAGResult(title=title, score=score, snippet=doc.splitlines()[0]))
        return results