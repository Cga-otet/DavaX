"""
Tooling: get_summary_by_title registered for function calling.
"""
import json, pathlib
from typing import Optional

BASE = pathlib.Path(__file__).parent
DATA_DICT_DIR = BASE / "book_data" / "summaries_dict.json"

def get_summary_by_title(title: str) -> str:
    data = json.loads(DATA_DICT_DIR.read_text(encoding="utf-8"))
    return data.get(title, "Nu am găsit un rezumat pentru acest titlu.")
