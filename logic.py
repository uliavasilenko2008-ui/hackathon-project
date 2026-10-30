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