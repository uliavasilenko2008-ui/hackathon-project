from data_loader import load_json
from config import RULES_PATH, TAXONOMY_PATH

for p in (RULES_PATH, TAXONOMY_PATH):
    d = load_json(p)
    print(p.name, type(d).__name__, list(d)[:5] if isinstance(d, dict) else len(d))
    first = d[list(d)[0]] if isinstance(d, dict) else d[0]
    print(type(first).__name__, list(first)[:8] if isinstance(first, dict) else str(first)[:80])