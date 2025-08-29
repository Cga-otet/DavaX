# Bibliotecar BookBot RAG (OpenAI + ChromaDB), author : Catalin Otet

Chatbot care recomandă carti în funcție de interesele utilizatorului,
folosind **GPT + RAG (ChromaDB)** și un **tool** ce returnează rezumatul complet al titlului recomandat.

## Incluse sunt
- `book_data/book_summaries.md` — bază de date cu carti 
- `book_data/summaries_dict.json` — dictionar pentru **get_summary_by_title(title: str)**
- `chroma_db_ingest.py` — script de init a vector store-ului Chroma (`text-embedding-3-small`)
- `chroma_db_retrieve.py` — retriever semantic pentru căutare după temă/context
- `tools.py` — implementare `get_summary_by_title`
- `librarian_app_cli.py` — chatbot in linie de comanda + function calling
- `librarian_streamlit.py` — acelasi chatbot dar in browser cu UI
- `requirements.txt` — dependinte pip
-  `chromadb_store/` — folder pt chroma db (initial gol)

## Setup
1. Instaleaza **Python 3.10+**.
2. Instalează pip req:
   ```bash
   pip install -r requirements.txt
   ```
3. Seteaza cheia:
   ```bash
   export OPENAI_API_KEY=YOUR_KEY
   ```
4. Creeaza colectia de carti `book_summaries`:
   ```bash
   python3 ingest.py
   ```

> Modelul de embeddings: `text-embedding-3-small`. 
> Folosesc modelele gpt-4o-mini.

## Rulare (CLI)
```bash
python3 librarian_app_cli.py
```
## Rulare Streamlit
```bash
streamlit run app_streamlit.py
```

Ex de întrebari:
- „Vreau o carte despre libertate și control social.”
- „Ce-mi recomanzi dacă iubesc poveștile fantastice?”
- „Vreau o poveste despre prietenie și magie.”
- „Ce este 1984?”

## How it works
1. **RAG**: user promtul este transformat in embedding (`text-embedding-3-small`) si cuatat in Chroma.
2. Sunt returnate top-N potriviri (titlu + snippet + scor).
3. **GPT** primeste intrebarea + rezultatele RAG si genereaza **recomandarea conversaționala**.
4. Modelul apeleaza automat tool-ul **`get_summary_by_title`** pentru titlul ales, iar mesajul final include **rezumatul complet** al celui mai bun match din lista returnata.

## Notite
- Filtru simplu de limbaj nepotrivit în CLI.

