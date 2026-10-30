# 1.ОБРАЩЕНИЕ:
...
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
...

class Message(BaseModel):
    role: Literal['player', 'reported_player', 'admin']
    ts: datetime
    text: str

class Ticket(BaseModel):
    ticket_id: str
    kind: Literal['complaint', 'report']
    created_at: datetime
    region: str
    server_language: Optional[str]
    language: Literal['ru', 'kk', 'en', 'es', 'pt', 'uz', 'unknown']
    reporter_hash: str
    reported_hash: Optional[str] = None
    reported_nick: Optional[str] = None
    rule_refs_raw: str
    images_count: int
    messages: List[Message]
    verdict: Literal['approved', 'rejected', 'need_evidence', 'invalid_format', 'duplicate']
    punishment: Optional[str] = None
    violation: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[Literal['p0', 'p1', 'p2', 'p3']] = None


# 2.НОРМАЛИЗАЦИЯ И ОПРЕДЕЛЕНИЕ ЯЗЫКА:
...
import re
from lingua import Language, LanguageDetectorBuilder
...

KZ_FIX = {'ќ': 'қ', 'ґ': 'ғ', 'ѕ': 'ң', 'є': 'ә', 'ј': 'ө', 'ў': 'ұ', 'ї': 'ү'}
KZ_LETTERS = set("қғңәөұүһі")

def normalize(text):
    text = text.lower()
    for bad, good in KZ_FIX.items():
        text = text.replace(bad, good)
    return text.strip()

# турецкий замена узбекскому (узбекского в lingua нет)
LATIN_DETECTOR = LanguageDetectorBuilder.from_languages(
    Language.ENGLISH, Language.SPANISH, Language.PORTUGUESE, Language.TURKISH
).build()

LANG_MAP = {
    Language.ENGLISH: 'en',
    Language.SPANISH: 'es',
    Language.PORTUGUESE: 'pt',
    Language.TURKISH: 'uz',
}

def detect_language(text):
    t = normalize(text)
    if any(ch in KZ_LETTERS for ch in t):
        return 'kk'
    if re.search(r'[а-яё]', t):
        return 'ru'
    if re.search(r'[a-z]', t):
        lang = LATIN_DETECTOR.detect_language_of(t)
        return LANG_MAP.get(lang, 'unknown')
    return 'unknown'


# 3.КАТЕГОРИИ:
HUMAN_TOPICS = {
    'payment': ['оплат','платеж', 'платёж', 'списан', 'возврат', 'төлем',
                'refund', 'payment', 'charge', 'pago', 'cobro', 'reembolso',
                'pagamento', "to'lov", 'tolov'],
    'ban_appeal': ['бан', 'заблок', 'блок', 'ban', 'block', 'bloque', 'blok'],
    'hack': ['взлом', 'угнал', 'hack', 'robaron', 'roubaram', 'buzil'],
}
OTHER_TOPICS = {
    'cheating': ['чит', 'cheat', 'trampa', 'trapaç'],
    'toxicity': ['оскорб', 'токсич', 'abuse', 'insult'],
    'bug': ['баг', 'вылет', 'ошибка', 'лаг', 'bug', 'crash', 'error'],
}
def count_hits(words, prefixes):
    hits = 0
    for word in words:
        word_ls = word.lower()
        if any(word_ls.startswith(p.lower()) for p in prefixes):
                hits += 1
    return hits


def classify(text):
    words = re.findall(r'\w+', text)

    for topic, prefix in HUMAN_TOPICS.items():
        if count_hits(words, prefix) > 0:
            return topic, True

    scores = {t: count_hits(words, p) for t, p in OTHER_TOPICS.items()}
    best = max(scores, key=scores.get)

    return (best, False) if scores[best] > 0 else ('other', False)

# 4.НЕ ПРОВЕРЕННЫЙ ДОНОС: