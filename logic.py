import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KZ_FIX = {'ќ': 'қ', 'ґ': 'ғ', 'ѕ': 'ң', 'є': 'ә', 'ј': 'ө', 'ў': 'ұ', 'ї': 'ү'}

def normalize(text):
    for bad, good in KZ_FIX.items():
        text = text.replace(bad, good)
        return text.lower().strip()

KZ_LETTERS = set("қғңәөұүһіҚҒҢӘӨҰҮҺІ")

def detect_language(text):
    text_lc = text.lower()

    if any(ch in KZ_LETTERS for ch in text):
        return 'kk'
    if len(re.findall(r'[а-яё]', text_lc)):
        return 'ru'
    if any(ch in 'ñáéíóúüü' for ch in text_lc):
        if any(ch in 'ãõçâêà' for ch in text_lc):
            return 'por'
        return 'esp'
    if len(re.findall(r'[a-z], text_lc')):
        if "'" in text_lc or "’" in text_lc:
            return 'uzb'
        return 'en'
    return 'unknown'

