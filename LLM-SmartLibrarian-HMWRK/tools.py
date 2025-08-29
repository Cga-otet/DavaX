import json, unicodedata, pathlib

BASE = pathlib.Path(__file__).parent
DATA_DICT_DIR = BASE / "book_data" / "summaries_dict.json"

def _normalize(s: str) -> str:
    if s is None:
        return ""
    return unicodedata.normalize("NFKC", s).strip().casefold()

def get_summary_by_title(title: str) -> str:
    data = json.loads(DATA_DICT_DIR.read_text(encoding="utf-8"))
    if title in data:
        return data[title]
    norm_map = {_normalize(k): v for k, v in data.items()}
    return norm_map.get(_normalize(title), "Nu am găsit un rezumat pentru acest titlu.")

