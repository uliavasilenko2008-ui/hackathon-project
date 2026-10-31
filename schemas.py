import json
import re
from typing import List, Literal, Optional
from pydantic import BaseModel

from logic import (normalize, detect_language, classify, draft_reply, RULES,
                   categorize, ALWAYS_HUMAN, PRIORITY, CAT_RULES)
from rules_model import predict_rule


# ВХОД:
class Message(BaseModel):
    role: Literal['player', 'reported_player', 'admin']
    text: str
    attachments: Optional[int] = 0


class IncomingTicket(BaseModel):
    kind: Literal['complaint', 'report']
    messages: List[Message]
    reported_nick: Optional[str] = None
    rule_refs_raw: Optional[str] = ""
    images_count: Optional[int] = 0
    region: Optional[str] = None


# ВЫХОД:
class ExtractedInfo(BaseModel):
    nickname: Optional[str] = None
    claimed_rule_refs: List[str] = []   # что написал игрок (ему верить нельзя)
    rule_refs: List[str] = []           # что нашли мы
    has_evidence: bool = False
    server: Optional[str] = None


class DraftReply(BaseModel):
    language: str
    text: str
    cited: List[str] = []


class FinalResponse(BaseModel):
    language: str
    category: str
    priority: str
    is_spam_or_duplicate: bool = False
    extracted: ExtractedInfo
    draft_reply: DraftReply
    needs_human: bool
    confidence: float
    reasons: List[str] = []


# ИЗВЛЕЧЕНИЕ ФАКТОВ:
def extract_nickname(ticket, raw_text):
    if ticket.reported_nick:
        return ticket.reported_nick
    m = re.search(r'[A-Z][a-z]+_[A-Z][a-z]+', raw_text)
    return m.group(0) if m else None


def extract_claimed_rules(ticket, raw_text):
    source = raw_text + " " + (ticket.rule_refs_raw or "")
    return sorted(set(re.findall(r'\b\d{1,2}(?:\.\d{1,2})+\b', source)))


def looks_like_spam(text):
    return len(text.strip()) < 3


# ГЛАВНАЯ ФУНКЦИЯ:
def build_response(ticket: IncomingTicket) -> FinalResponse:
    player_msgs = [m for m in ticket.messages if m.role == "player"]
    raw_text = " ".join(m.text for m in player_msgs)
    text = normalize(raw_text)
    attachments = sum((m.attachments or 0) for m in ticket.messages)
    attachments += ticket.images_count or 0

    language = detect_language(text)
    topic, human = classify(text)
    rule, prob = predict_rule(text)
    rule_ids = [rule] if rule and rule in RULES else []
    claimed = extract_claimed_rules(ticket, raw_text)

    category = categorize(ticket.kind, topic, rule_ids if prob >= 0.7 else [])
    allowed = CAT_RULES.get(category, [])
    rule_ids = [r for r in rule_ids
                if ("GZ" if r.startswith("32:") else r.split(":")[1]) in allowed]

    reasons = []
    if human:
        reasons.append("платежи, баны и взлом всегда решает человек")
    if category in ALWAYS_HUMAN:
        human = True
        reasons.append("эта категория всегда требует человека")
    if not rule_ids:
        human = True
        reasons.append("не найден подходящий пункт правил")
    found_refs = {r.split(":")[1] for r in rule_ids}
    if claimed and rule_ids and not (set(claimed) & found_refs):
        human = True
        reasons.append("игрок назвал другой пункт, чем найден по тексту")
    if language == "unknown":
        human = True
        reasons.append("не удалось определить язык")

    priority = PRIORITY.get(category, "p2")
    if topic in ("payment", "hack"):
        priority = "p0"
    elif ticket.kind == "complaint" and attachments > 0 and priority in ("p2", "p3"):
        priority = "p1"

    return FinalResponse(
        language=language,
        category=category,
        priority=priority,
        is_spam_or_duplicate=looks_like_spam(raw_text),
        extracted=ExtractedInfo(
            nickname=extract_nickname(ticket, raw_text),
            claimed_rule_refs=claimed,
            rule_refs=rule_ids,
            has_evidence=attachments > 0,
            server=ticket.region,
        ),
        draft_reply=DraftReply(
            language=language,
            text=draft_reply(language, rule_ids, human),
            cited=rule_ids,
        ),
        needs_human=human,
        confidence=round(prob, 2),
        reasons=reasons,
    )


def process_file_ticket(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return build_response(IncomingTicket(**data)).model_dump_json(
        indent=2, ensure_ascii=False)


if __name__ == "__main__":
    demo = IncomingTicket(
        kind="complaint",
        messages=[Message(role="player",
                          text="Игрок оскорбил меня и мою маму в чате",
                          attachments=0)],
    )
    print(build_response(demo).model_dump_json(indent=2, ensure_ascii=False))