import re
from lingua import Language, LanguageDetectorBuilder
from config import RULES_PATH, TAXONOMY_PATH
from data_loader import load_json


# 1.НОРМАЛИЗАЦИЯ И ЯЗЫК:
KZ_FIX = {'ќ': 'қ', 'ґ': 'ғ', 'ѕ': 'ң', 'є': 'ә', 'ј': 'ө', 'ў': 'ұ', 'ї': 'ү'}
KZ_LETTERS = set("қғңәөұүһі")


def normalize(text):
    text = text.lower()
    for bad, good in KZ_FIX.items():
        text = text.replace(bad, good)
    return text.strip()


# турецкий как замена узбекскому (узбекского в lingua нет)
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


# 2.ТЕМЫ:
HUMAN_TOPICS = {
    'payment': ['оплат', 'платеж', 'платёж', 'списан', 'возврат', 'төлем',
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
        if any(word.lower().startswith(p.lower()) for p in prefixes):
            hits += 1
    return hits


def classify(text):
    words = re.findall(r'\w+', text)
    for topic, prefixes in HUMAN_TOPICS.items():
        if count_hits(words, prefixes) > 0:
            return topic, True
    scores = {t: count_hits(words, p) for t, p in OTHER_TOPICS.items()}
    best = max(scores, key=scores.get)
    return (best, False) if scores[best] > 0 else ('other', False)


# 3.ПРАВИЛА:
def load_rules():
    rules = {}
    try:
        for sec in load_json(RULES_PATH)["rules"]:
            for p in sec.get("points", []):
                rules[f"{sec['id']}:{p['ref']}"] = p["text"]
    except FileNotFoundError:
        pass
    return rules or {"0:0": "Тестовое правило: запрещены читы."}


RULES = load_rules()


# 4.КАТЕГОРИЯ И ПРИОРИТЕТЫ:
try:
    TAX = load_json(TAXONOMY_PATH)
except FileNotFoundError:
    TAX = {"categories": [], "needs_human_always": []}

ALWAYS_HUMAN = set(TAX["needs_human_always"])
CAT_KIND = {c["code"]: c["kind"] for c in TAX["categories"]}
RULE_TO_CAT = {}
for c in TAX["categories"]:
    for r in c["rules"]:
        RULE_TO_CAT.setdefault(r, c["code"])
        CAT_RULES = {c["code"]: c["rules"] for c in TAX["categories"]}

TOPIC_TO_CAT = {
    "payment": "report.payment", "hack": "report.account",
    "ban_appeal": "complaint.admin", "cheating": "complaint.cheat",
    "toxicity": "complaint.insult", "bug": "report.help",
}

# ПРЕДПОЛОЖЕНИЕ:
PRIORITY = {
    "report.account": "p0", "report.payment": "p0",
    "complaint.cheat": "p1", "complaint.scam": "p1", "complaint.rmt_ads": "p1",
    "complaint.insult": "p2", "complaint.dm": "p2", "complaint.admin": "p2",
    "report.complaint": "p2",
    "complaint.other": "p3", "complaint.invalid": "p3", "report.question": "p3",
    "report.help": "p3", "report.offtopic": "p3",
}


def categorize(kind, topic, rule_ids):
    cat = TOPIC_TO_CAT.get(topic)
    if cat is None and rule_ids:
        sec, ref = rule_ids[0].split(":")
        if sec == "32":
            cat = RULE_TO_CAT.get("GZ")
        elif sec == "30":
            cat = RULE_TO_CAT.get(ref)
    if CAT_KIND.get(cat) != kind:
        if kind == "report" and cat and cat.startswith("complaint."):
            cat = "report.complaint"
        else:
            cat = "complaint.other" if kind == "complaint" else "report.question"
    return cat


# 5.ЧЕРНОВИК ОТВЕТА:
TEMPLATES = {
    "ru": "Здравствуйте! Спасибо за обращение. Мы изучим ситуацию{refs}.",
    "en": "Hello! Thank you for your report. We will review the situation{refs}.",
    "kk": "Сәлеметсіз бе! Хабарласқаныңыз үшін рахмет. Жағдайды қарастырамыз{refs}.",
    "es": "¡Hola! Gracias por su mensaje. Revisaremos la situación{refs}.",
    "pt": "Olá! Obrigado pelo seu contato. Vamos analisar a situação{refs}.",
    "uz": "Salom! Murojaatingiz uchun rahmat. Vaziyatni ko'rib chiqamiz{refs}.",
}
HUMAN_TEMPLATES = {
    "ru": "Здравствуйте! Ваше обращение передано специалисту поддержки.",
    "en": "Hello! Your request has been passed to a support specialist.",
    "kk": "Сәлеметсіз бе! Сіздің өтінішіңіз қолдау маманына жіберілді.",
    "es": "¡Hola! Su solicitud ha sido transferida a un especialista de soporte.",
    "pt": "Olá! Seu pedido foi encaminhado a um especialista de suporte.",
    "uz": "Salom! Murojaatingiz qo'llab-quvvatlash mutaxassisiga yuborildi.",
}


def draft_reply(lang, rule_ids, human):
    lang = lang if lang in TEMPLATES else "en"
    if human:
        return HUMAN_TEMPLATES[lang]
    refs = f" (п. {', '.join(rule_ids)})" if rule_ids else ""
    return TEMPLATES[lang].format(refs=refs)