import re
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import make_pipeline
from config import TRAIN_PATH, DATA_DIR
from data_loader import read_jsonl
from logic import RULES

MODEL_PATH = DATA_DIR / "rule_model.pkl"   # лежит в data/, в Git не попадает
_model = None

# ГИПОТЕЗА: ОП = раздел 30 (общие правила), GZ = раздел 32 (зелёная зона)
TAG_TO_SECTION = {"ОП": "30", "OP": "30", "GZ": "32"}


def clean_rule(v):
    s = str(v or "").upper()
    ref = re.search(r"\d+(?:\.\d+)+", s)
    tag = re.search(r"(ОП|OP|GZ)", s)
    if not ref or not tag:
        return None
    key = f"{TAG_TO_SECTION[tag.group(1)]}:{ref.group(0)}"
    return key if key in RULES else None


def player_text(t):
    return " ".join(m["text"] for m in t.get("messages", [])
                    if m.get("role") == "player").lower()


def train(limit=60000):
    X, y = [], []
    for t in read_jsonl(TRAIN_PATH):
        rule = clean_rule(t.get("violation"))
        if rule:
            X.append(player_text(t))
            y.append(rule)
        if len(X) >= limit:
            break
    if not X:
        raise RuntimeError("Нет примеров с пунктами: проверь clean_rule и RULES")
    model = make_pipeline(
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=200000),
        SGDClassifier(loss="log_loss", max_iter=15, random_state=0),
    )
    model.fit(X, y)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    return model


def get_model():
    global _model
    if _model is None:
        if MODEL_PATH.exists():
            with open(MODEL_PATH, "rb") as f:
                _model = pickle.load(f)
        else:
            _model = train()
    return _model


def predict_rule(text, threshold=0.5):
    model = get_model()
    proba = model.predict_proba([text.lower()])[0]
    i = proba.argmax()
    if proba[i] >= threshold:
        return str(model.classes_[i]), float(proba[i])
    return None, float(proba[i])


if __name__ == "__main__":
    m = train()
    print(len(m.classes_), list(m.classes_)[:10])
    print(RULES.get("30:2.1", "")[:150])
    print(RULES.get("32:1.2", "")[:150])