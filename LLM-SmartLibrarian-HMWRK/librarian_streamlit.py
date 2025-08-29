import pathlib
import streamlit as st
from openai import OpenAI
from chroma_db_retrieve import Retriever
from tools import get_summary_by_title

BASE = pathlib.Path(__file__).parent
DB_DIR = str(BASE / "chromadb_store")

st.set_page_config(page_title="BookBot RAG", page_icon="📚")
st.title("Librarian BookBot RAG")
st.caption("Recomandări de cărți pe teme + rezumat (alege scorul cel mai mare)")

client = OpenAI()
retriever = Retriever(persist_dir=DB_DIR)

BANNED = {"idiot", "stupid", "fuck", "shit", "dumb", "bastard", "crap", "suck", "damn", "cunt"}
def blocked(text: str) -> bool:
    t = (text or "").lower()
    return any(b in t for b in BANNED)

q = st.text_input("Ce fel de carte cauți?", placeholder="ex. Vreau o carte fantasy")
if st.button("Recomandă"):
    if not q.strip():
        st.warning("Scrie o întrebare.")
        st.stop()
    if blocked(q):
        st.warning("Prefer să păstrăm conversația politicoasă. Te rog reformulează fără limbaj nepotrivit.")
        st.stop()

    with st.spinner("Caut potriviri..."):
        hits = retriever.search(q, top_k=3)

    if not hits:
        st.info("Nu am găsit potriviri.")
        st.stop()

    hits = sorted(hits, key=lambda h: float(h.score), reverse=True)
    top_title = hits[0].title

    st.subheader("Potriviri găsite (după scor)")
    for h in hits:
        st.markdown(f"**{h.title}** · scor: {float(h.score):.3f}")
        st.caption(h.snippet)

    # tool simplu
    tools = [{
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

    # 3) promptul: vorbește despre cartea cu scorul cel mai mare
    system = (
        "Ești un asistent care recomandă cărți pe baza rezultatelor RAG.\n"
        "Alege ÎNTOTDEAUNA cartea cu SCORUL CEL MAI MARE dintre candidați și vorbește despre ea (în română)."
    )
    rag_lines = "\n".join(f"- {h.title} | {float(h.score):.3f} | {h.snippet}" for h in hits)
    user = f"Întrebare: {q}\nCandidați (titlu | scor | snippet):\n{rag_lines}"

    # 4) cere modelului + force un apel de tool
    resp = client.responses.create(
        model="gpt-4o-mini",
        input=[{"role": "system", "content": system},
               {"role": "user", "content": user}],
        tools=tools,
        tool_choice={"type": "function", "name": "get_summary_by_title"}
    )

    # 5) colectează apelul de tool 
    def get_first_function_call(response):
        for item in (getattr(response, "output", None) or []):
            if getattr(item, "type", None) == "function_call":
                return item  # fields: name, arguments, call_id
            if getattr(item, "type", None) == "tool_call" and getattr(item, "tool_call", None):
                tc = item.tool_call
                return type("FC", (), {
                    "name": getattr(getattr(tc, "function", None), "name", None),
                    "arguments": getattr(getattr(tc, "function", None), "arguments", None),
                    "call_id": getattr(tc, "id", None) or getattr(tc, "call_id", None),
                })
            if getattr(item, "type", None) == "message":
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

    fc = get_first_function_call(resp)
    if not fc or not getattr(fc, "call_id", None):
        st.error("Modelul n-a apelat tool-ul. Încearcă din nou.")
        st.stop()

    # 6) rezumat pentru titlul cu scorul cel mai mare
    summary = get_summary_by_title(top_title)

    final = client.responses.create(
    model="gpt-4o-mini",
    previous_response_id=resp.id, 
    input=[
        {
            "type": "function_call_output",
            "call_id": fc.call_id, 
            "output": summary       
        }
    ]
    )

    # 7) extrage textul final + fallback
    def extract_text(r):
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

    content = extract_text(final)

    st.markdown("### Răspuns")
    st.markdown(f"_Titlu recomandat (scor maxim): **{top_title}**_")
    if content:
        st.write(content)
    else:
        st.markdown("**Rezumat:**")
        st.write(summary)
