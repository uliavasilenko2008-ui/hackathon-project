import time
from config import VALID_PATH
from data_loader import read_jsonl
from logic import normalize, detect_language
from rules_model import clean_rule, predict_rule
from schemas import IncomingTicket, build_response

n = lang_ok = human = 0
rule_total = rule_ok = 0
t0 = time.time()
for raw in read_jsonl(VALID_PATH):
    n += 1
    ticket = IncomingTicket(**raw)
    resp = build_response(ticket)
    lang_ok += resp.language == raw.get("lang")
    human += resp.needs_human
    gold = clean_rule(raw.get("violation"))
    if gold:
        rule_total += 1
        text = normalize(" ".join(m.text for m in ticket.messages if m.role == "player"))
        rule_ok += predict_rule(text)[0] == gold
dt = (time.time() - t0) / n * 1000

print(f"Тикетов: {n}")
print(f"Язык: {lang_ok / n:.1%}")
print(f"Пункт правил: {rule_ok}/{rule_total} = {rule_ok / max(rule_total, 1):.1%}")
print(f"Нужен человек: {human / n:.1%}")
print(f"Время на тикет: {dt:.1f} мс")