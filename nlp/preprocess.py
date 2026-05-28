import re
import html
import hashlib
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


def clean_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


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
