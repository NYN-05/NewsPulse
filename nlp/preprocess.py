import re
import html
import hashlib
import unicodedata
import logging
from functools import lru_cache
from config.settings import get

logger = logging.getLogger(__name__)

SENSATIONAL_WORDS = {
    "shocking", "stunning", "explosive", "massive", "terrifying", "heartbreaking",
    "devastating", "unbelievable", "dramatic", "furious", "outrage", "slams",
    "blasts", "war", "crisis", "disaster", "tragedy", "horror", "nightmare",
    "chaos", "panic", "emergency", "deadly", "fatal", "brutal", "violent",
    "attack", "killer", "destroy", "collapse", "plunge", "crash", "surge",
    "spike", "epidemic", "scandal", "controversy", "feud", "rivalry",
    "battle", "fight", "clash", "rift", "split", "turmoil", "upheaval",
    "crackdown", "purge", "ban", "oust", "dump", "axed", "fired", "sacked",
}

_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
_EMOJI_PATTERN = re.compile(
    "[" u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF"
    u"\U0001F680-\U0001F6FF" u"\U0001F1E0-\U0001F1FF"
    u"\U00002702-\U000027B0" u"\U000024C2-\U0001F251"
    u"\U0001F900-\U0001F9FF" u"\U0000200D" u"\U0000FE0F"
    u"\U0000200B" u"\U0000200C" u"\U0000FE0E" u"\U00002B50"
    u"\U0001F004-\U0001F0CF" u"\U00002600-\U000026FF"
    u"\U0001F000-\U0001F02F" u"\U0001F0A0-\U0001F0FF"
    u"\U0001F100-\U0001F64F" u"\U0001F680-\U0001F6FF"
    "]+", flags=re.UNICODE)


def _normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def _strip_emojis(text: str) -> str:
    return _EMOJI_PATTERN.sub("", text)


def _strip_urls(text: str) -> str:
    return _URL_PATTERN.sub("", text)


def clean_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""
    text = html.unescape(text)
    text = _normalize_unicode(text)
    text = _strip_emojis(text)
    text = _strip_urls(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


@lru_cache(maxsize=2048)
def _cached_category_extraction(title: str):
    if not isinstance(title, str) or not title.strip():
        return None, ""
    m = re.match(r"^([A-Za-z\s&]+?)(?=[A-Z]|\d)", title)
    if m:
        cat = m.group(1).strip()
        rest = title[len(cat):].strip()
        if rest:
            return cat, rest
    return None, title


def extract_category(title: str):
    return _cached_category_extraction(title)


@lru_cache(maxsize=2048)
def _cached_sensationalism(text: str) -> float:
    if not isinstance(text, str) or not text.strip():
        return 0.0
    words = set(re.findall(r"\w+", text.lower()))
    if not words:
        return 0.0
    return round(len(words & SENSATIONAL_WORDS) / len(words), 4)


def detect_sensationalism(text: str) -> float:
    return _cached_sensationalism(text)


def hash_content(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()
