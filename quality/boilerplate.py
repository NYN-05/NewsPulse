import re
import logging

logger = logging.getLogger(__name__)

BOILERPLATE_PATTERNS = [
    r"click here to subscribe",
    r"subscribe to our newsletter",
    r"sign up for our newsletter",
    r"read more",
    r"related stories",
    r"related articles",
    r"also read",
    r"also watch",
    r"trending now",
    r"top stories",
    r"more from",
    r"follow us on",
    r"share this article",
    r"comments are closed",
    r"this article was originally published",
    r"© \d{4}",
    r"all rights reserved",
    r"terms of service",
    r"privacy policy",
    r"cookie policy",
    r"advertise with us",
    r"contact us",
    r"about us",
    r"your email address",
    r"email address",
    r"photo credit",
    r"image credit",
    r"source:",
    r"via:",
    r"courtesy:",
    r"reuters\s*$",
    r"associated press\s*$",
    r"^(i|we)\s+have\s+updated\s+this\s+article",
    r"^(this|the)\s+(story|article|report)\s+(has been|was)",
    r"^editor'?s?\s+(note|pick)",
    r"^disclaimer",
]


def remove_boilerplate(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""
    lines = text.split("\n")
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if len(stripped) < 15:
            continue
        lower = stripped.lower()
        is_boiler = False
        for pat in BOILERPLATE_PATTERNS:
            if re.search(pat, lower):
                is_boiler = True
                break
        if not is_boiler:
            clean_lines.append(stripped)
    return " ".join(clean_lines)


def extract_clean_title(raw_title: str) -> str:
    if not isinstance(raw_title, str):
        return ""
    title = raw_title.strip()
    title = re.sub(r"\s*\|\s*.*$", "", title)
    title = re.sub(r"\s*-\s*.*$", "", title)
    title = re.sub(r"\s*–\s*.*$", "", title)
    title = re.sub(r"\s*:.*$", "", title)
    title = re.sub(r"\s*«.*$", "", title)
    return title.strip()
