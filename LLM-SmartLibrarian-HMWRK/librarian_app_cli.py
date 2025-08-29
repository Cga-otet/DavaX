import os, json, pathlib
from openai import OpenAI
from chroma_db_retrieve import Retriever
from tools import get_summary_by_title

BASE = pathlib.Path(__file__).parent
DB_DIR = str(BASE / "chromadb_store")

BANNED = {"idiot", "stupid", "fuck", "shit", "dumb", "bastard", "crap", "suck", "damn", "cunt"}
def blocked(text: str) -> bool:
    t = (text or "").lower()
    return any(b in t for b in BANNED)

def build_tools_schema() -> list[dict]:
    return [{
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
    }]

def get_first_function_call(response):
    """Robustly extract the first function call across SDK shapes."""
    for item in (getattr(response, "output", None) or []):
        t = getattr(item, "type", None)
        if t == "function_call":
            # fields: name, arguments, call_id
            return item
        if t == "tool_call" and getattr(item, "tool_call", None):
            tc = item.tool_call
            return type("FC", (), {
                "name": getattr(getattr(tc, "function", None), "name", None),
                "arguments": getattr(getattr(tc, "function", None), "arguments", None),
                "call_id": getattr(tc, "id", None) or getattr(tc, "call_id", None),
            })
        if t == "message":
            msg = getattr(item, "message", None)
            tcs = getattr(msg, "tool_calls", None) or []
            if tcs:
                tc = tcs[0]
                return type("FC", (), {
                    "name": getattr(getattr(tc, "function", None), "name", None),
                    "arguments": getattr(getattr(tc, "function", None), "arguments", None),
                    "call_id": getattr(tc, "id", None) or getattr(tc, "call_id", None),
                })
    return None

def extract_text(r):
    """Get final text from a Responses object (with fallback)."""
    t = (getattr(r, "output_text", None) or "").strip()
    if t:
        return t
    parts = []
    for item in (getattr(r, "output", None) or []):
        if getattr(item, "type", None) == "message":
            msg = item.message
            for c in (getattr(msg, "content", None) or []):
                if getattr(c, "type", None) == "output_text" and getattr(c, "text", None):
                    parts.append(c.text)
    return "\n".join(parts).strip()

def run_cli():
    client = OpenAI()
    retriever = Retriever(persist_dir=DB_DIR)

    print("BookBot RAG • tastează 'exit' pentru a-l închide.\n")
    while True:
        q = input("Tu: ").strip()
        if q.lower() in {"exit", "quit"}:
            print("La revedere!")
            break
        if not q:
            continue
        if blocked(q):
            print("Asistent: Prefer să păstrăm conversația politicoasă. Te rog reformulează fără limbaj nepotrivit.")
            continue

        # 1) RAG
        hits = retriever.search(q, top_k=3)
        if not hits:
            print("Asistent: Nu am găsit potriviri în colecție.\n")
            continue

        hits = sorted(hits, key=lambda h: float(h.score), reverse=True)
        top_title = hits[0].title

        print("\nPotriviri găsite (după scor):")
        for h in hits:
            print(f"- {h.title} | {float(h.score):.3f} | {h.snippet[:120]}")

        # 2) prompts + tool schema
        system = (
            "Ești un asistent care recomandă cărți pe baza rezultatelor RAG.\n"
            "Alege ÎNTOTDEAUNA cartea cu SCORUL CEL MAI MARE și vorbește despre ea (în română)."
        )
        rag_lines = "\n".join(f"- {h.title} | {float(h.score):.3f} | {h.snippet}" for h in hits)
        user = f"Întrebare: {q}\nCandidați (titlu | scor | snippet):\n{rag_lines}"

        tools = build_tools_schema()

        # 3) ask model + force one function call
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=[{"role": "system", "content": system},
                   {"role": "user", "content": user}],
            tools=tools,
            tool_choice={"type": "function", "name": "get_summary_by_title"}
        )

        # 4) find function call 
        fc = get_first_function_call(resp)
        if not fc or not getattr(fc, "call_id", None):
            # pt debug
            # print(resp.model_dump())
            print("\nAsistent: Modelul n-a apelat tool-ul. Încearcă din nou.\n")
            continue

        # 5) run local tool for the TOP title 
        summary = get_summary_by_title(top_title)

        # 6) reply to that function call with a second Responses call
        final = client.responses.create(
            model="gpt-4o-mini",
            previous_response_id=resp.id,
            input=[{
                "type": "function_call_output",
                "call_id": fc.call_id,
                "output": summary
            }]
        )

        # 7) print final text / fallback
        content = extract_text(final)
        print(f"\nAsistent (Titlu recomandat: {top_title}):\n{content or summary}\n")

if __name__ == "__main__":
    run_cli()
