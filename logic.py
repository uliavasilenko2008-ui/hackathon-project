# 1.ОБРАЩЕНИЕ:
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from lingua import Language, LanguageDetectorBuilder
from config import RULES_PATH
from data_loader import load_json


# 2.НОРМАЛИЗАЦИЯ И ОПРЕДЕЛЕНИЕ ЯЗЫКА:
import re
from lingua import Language, LanguageDetectorBuilder

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

#  ПРАВИЛА:
def flatten_rules(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str) and re.fullmatch(r"\d+(\.\d+)*", str(k)):
                out[str(k)] = v
        rid = next((node[k] for k in ("id", "point_id", "point", "number", "num", "code") if k in node), None)
        txt = next((node[k] for k in ("text", "title", "description", "rule", "name")
                    if isinstance(node.get(k), str)), None)
        if rid is not None and txt:
            out[str(rid)] = txt
        for v in node.values():
            flatten_rules(v, out)
    elif isinstance(node, list):
        for item in node:
            flatten_rules(item, out)


def load_rules():
    rules = {}
    try:
        flatten_rules(load_json(RULES_PATH), rules)
    except FileNotFoundError:
        pass
    return rules or {"0.0": "Тестовое правило: запрещены читы."}


RULES = load_rules()


def find_rules(text, top=2, threshold=0.1):
    ids = list(RULES)
    if not ids:
        return []

    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
    matrix = vec.fit_transform([RULES[i].lower() for i in ids] + [text.lower()])

    # Считаем схожесть
    sims_matrix = cosine_similarity(matrix[-1], matrix[:-1])

    if sims_matrix.shape[0] > 0:
        sims = sims_matrix[0]
    else:
        return []

    ranked = sorted(zip(ids, sims), key=lambda p: p[1], reverse=True)
    return [i for i, s in ranked[:top] if s >= threshold]

# ЧЕРНОВИК ОТВЕТА:
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

# 4.НЕ ПРОВЕРЕННЫЙ ДОНОС:

print(len(RULES), list(RULES)[:5])