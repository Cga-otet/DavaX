"""
Build a ChromaDB collection from data/book_summaries.md using OpenAI embeddings.
"""

import os, re, uuid, json, pathlib
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from openai import OpenAI

BASE_DIR = pathlib.Path(__file__).parent
DATA_MD_DIR = BASE_DIR / "book_data" / "book_summaries.md"
DATA_DICT_DIR = BASE_DIR / "book_data" / "summaries_dict.json"
DB_DIR = BASE_DIR / "chromadb_store"

EMBED_MODEL = "text-embedding-3-small"

# Read books from md file and put into a dictionary
def load_books(md_path: pathlib.Path) -> List[Dict]:
    text = md_path.read_text(encoding="utf-8")
    blocks = re.split(r"\n(?=## Title: )", text.strip())
    items = []
    # Extract title and content from each block matching regex
    for b in blocks:
        m = re.match(r"## Title:\s*(.+)\n(.+)", b, flags=re.DOTALL)
        if not m: 
            continue
        title = m.group(1).strip()
        content = m.group(2).strip()
        items.append({"title": title, "content": content})
    return items

def embed_texts(client: OpenAI, texts: List[str]) -> List[List[float]]:
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]

def main():
    # Initialize OpenAI client
    client = OpenAI()
    items = load_books(DATA_MD_DIR)
    if not items:
        raise RuntimeError("No items parsed from book_summaries.md")
    # Init Chroma
    client_db = chromadb.PersistentClient(path=str(DB_DIR))
    coll = client_db.get_or_create_collection("book_summaries")
    # Clear existing data
    try:
        existing = coll.get()
        if existing and existing.get("ids"):
            coll.delete(ids=existing["ids"])
    except Exception:
        pass
    # Upsert
    texts = [i["content"] for i in items]
    titles = [i["title"] for i in items]
    embeddings = embed_texts(client, texts)
    ids = [str(uuid.uuid4()) for _ in items]
    coll.add(ids=ids, embeddings=embeddings, metadatas=[{"title": t} for t in titles], documents=texts)
    print(f"Indexed {len(items)} books into collection 'book_summaries' at {DB_DIR}")
    print("Done.")

if __name__ == "__main__":
    main()
