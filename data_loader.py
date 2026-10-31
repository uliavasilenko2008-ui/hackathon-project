import gzip
import json


def read_jsonl(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)