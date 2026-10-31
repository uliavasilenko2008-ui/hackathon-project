from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

TRAIN_PATH = DATA_DIR / "tickets_train.jsonl.gz"
VALID_PATH = DATA_DIR / "tickets_valid.jsonl"
RULES_PATH = DATA_DIR / "rules.json"
TAXONOMY_PATH = DATA_DIR / "taxonomy.json"