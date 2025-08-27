#!/usr/bin/env python3
import os, sys, json, pathlib
from typing import Dict, Any
from openai import OpenAI
from chroma_db_retrieve import Retriever
from tools import get_summary_by_title

BASE = pathlib.Path(__file__).parent
DB_DIR = str(BASE / "chromadb_store")

# Banned words list and checking function
BANNED = {"idiot", "stupid", "fuck", "shit"}

def blocked(text: str) -> bool:
    t = text.lower()
    return any(b in t for b in BANNED)

def build_tools_schema() -> list[dict]:
    return [
        {
            "type": "function",
            "name": "get_summary_by_title",
            "description": "Returnează rezumatul complet pentru un titlu de carte exact.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Titlul exact al cărții."}
                },
                "required": ["title"],
                "additionalProperties": False
            }
        }
    ]


def run_cli(voice: bool = False, image: bool = False, tts: bool = False):
    client = OpenAI()
    retriever = Retriever(persist_dir=DB_DIR)
    print("BookBot RAG • tasteaza 'exit' pentru a-l închide.\n")
    while True:
        q = input("Tu: ").strip()
        if q.lower() in {"exit", "quit"}:
            print("La revedere!")
            break
        if blocked(q):
            print("Asistent: Prefer să păstrăm conversația politicosă. Te rog reformulează fără limbaj nepotrivit.")
            continue

        # 1) Retrieve candidates from Chroma by theme/context
        hits = retriever.search(q, top_k=3)
        if not hits:
            print("Asistent: Nu am găsit potriviri în colecție.")
            continue

        # 2) Ask GPT to pick the best book and produce a conversational recommendation
        system = (
            "Ești un asistent care recomandă cărți. "
            "Ai la dispoziție rezultate dintr-un vector store. "
            "Alege cea mai potrivită carte și răspunde conversațional în română. "
            "La final, vei apela tool-ul get_summary_by_title cu titlul ales."
        )
        user = f"Întrebare: {q}\nRezultate RAG (titlu | scor | snippet):\n" + "\n".join(
            f"- {h.title} | {h.score:.3f} | {h.snippet}" for h in hits
        )
        tools = build_tools_schema()
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role":"system","content":system},
                {"role":"user","content":user}
            ],
            tools=tools
        )

        # 3) If the model wants to call our tool, do it and then send back the result
        if resp.output and resp.output[0].type == "tool_calls":
            # Assume first tool call has the title
            for call in resp.output[0].tool_calls:
                if call.function.name == "get_summary_by_title":
                    args = json.loads(call.function.arguments or "{}")
                    title = args.get("title","").strip()
                    summary = get_summary_by_title(title) if title else "Titlu lipsă."
                    # Send tool result back to the model to produce final answer
                    tool_msg = {
                        "tool_call_id": call.id,
                        "output": summary
                    }
                    final = client.responses.create(
                        model="gpt-4o-mini",
                        input=[
                            {"role":"system","content":system},
                            {"role":"user","content":user},
                            {"role":"tool","content":tool_msg}
                        ]
                    )
                    print("\nAsistent:", final.output_text.strip(), "\n")
                    break
        else:
            # If the model already produced text, show it, then append the full summary of top-1 as fallback
            recommendation_text = resp.output_text.strip()
            top_title = hits[0].title
            full_summary = get_summary_by_title(top_title)
            print("\nAsistent:", recommendation_text)
            print(f"\nRezumat complet pentru '{top_title}':\n{full_summary}\n")

if __name__ == "__main__":
    run_cli()
