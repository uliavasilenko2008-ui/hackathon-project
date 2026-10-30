import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
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


