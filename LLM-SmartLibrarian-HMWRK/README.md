# BookBot RAG (OpenAI + ChromaDB)

Chatbot care recomandă cărți în funcție de interesele utilizatorului,
folosind **GPT + RAG (ChromaDB)** și un **tool** ce returnează rezumatul complet al titlului recomandat.

## Ce include
- `book_data/book_summaries.md` — bază de date cu 12+ cărți (titlu + rezumat scurt + teme)
- `book_data/summaries_dict.json` — sursa locală pentru **get_summary_by_title(title: str)**
- `chroma_db_ingest.py` — script de inițializare a vector store-ului Chroma (embeddings OpenAI `text-embedding-3-small`)
- `chroma_db_retrieve.py` — retriever semantic pentru căutare după temă/context
- `tools.py` — implementare `get_summary_by_title`
- `librarian_app_cli.py` — chatbot în linie de comandă (cu function calling + fallback)
- `requirements.txt` — dependințe
- directorul `chromadb_store/` — persistent store (inițial gol)

## Setup
1. **Python 3.10+** recomandat.
2. Instalează dependențele:
   ```bash
   pip install -r requirements.txt
   ```
3. Setează cheia:
   ```bash
   export OPENAI_API_KEY=YOUR_KEY
   ```
4. Inițializează vector store-ul (creează colecția `book_summaries`):
   ```bash
   python3 ingest.py
   ```

> Modelul de embeddings: `text-embedding-3-small` (OpenAI) — vezi documentația oficială.  
> Conversație/Function calling/TTS folosesc modelele GPT-4o/gpt-4o-mini/gpt-4o-mini-tts.

## Rulare (CLI)
```bash
python3 librarian_app_cli.py
```
Exemple de întrebări:
- „Vreau o carte despre libertate și control social.”
- „Ce-mi recomanzi dacă iubesc poveștile fantastice?”
- „Vreau o poveste despre prietenie și magie.”
- „Ce este 1984?”

## Cum funcționează
1. **RAG**: întrebarea utilizatorului este transformată în embedding (`text-embedding-3-small`) și căutată în Chroma.
2. Sunt returnate top-N potriviri (titlu + snippet + scor).
3. **GPT** primește întrebarea + rezultatele RAG și generează **recomandarea conversațională**.
4. Modelul apelează automat tool-ul **`get_summary_by_title`** pentru titlul ales, iar mesajul final include **rezumatul complet**.

## Notițe
- Nu folosim vector store-ul OpenAI — doar ChromaDB local.
- Filtru simplu de limbaj nepotrivit în CLI.

