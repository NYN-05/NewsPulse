import logging
from typing import Optional

logger = logging.getLogger(__name__)

_lang_detector = None


def _get_detector():
    global _lang_detector
    if _lang_detector is not None:
        return _lang_detector
    try:
        from fasttext import load_model
        import os
        model_path = os.path.join(os.path.dirname(__file__), "..", "models", "lid.176.bin")
        if os.path.exists(model_path):
            _lang_detector = load_model(model_path)
            logger.info("fastText language detector loaded")
        else:
            logger.info("fastText model not found at %s, using langdetect fallback", model_path)
            _lang_detector = "langdetect"
    except ImportError:
        logger.info("fasttext not installed, using langdetect fallback")
        _lang_detector = "langdetect"
    return _lang_detector


def detect_language(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return "unknown"
    detector = _get_detector()
    if detector is None:
        return "unknown"
    if detector == "langdetect":
        try:
            from langdetect import detect
            return detect(text[:500])
        except Exception:
            return "unknown"
    try:
        preds = detector.predict(text[:500].replace("\n", " "))
        lang = preds[0][0].replace("__label__", "")
        return lang
    except Exception as e:
        logger.debug("Language detection failed: %s", e)
        return "unknown"


INDIAN_LANGUAGES = {
    "hi": "Hindi", "bn": "Bengali", "te": "Telugu", "mr": "Marathi",
    "ta": "Tamil", "ur": "Urdu", "gu": "Gujarati", "kn": "Kannada",
    "ml": "Malayalam", "or": "Odia", "pa": "Punjabi", "as": "Assamese",
    "mai": "Maithili", "sat": "Santali", "ks": "Kashmiri", "ne": "Nepali",
    "sd": "Sindhi", "kok": "Konkani", "doi": "Dogri", "mni": "Manipuri",
    "bho": "Bhojpuri", "mag": "Magahi", "raj": "Rajasthani", "hne": "Chhattisgarhi",
}


def is_indian_language(lang_code: str) -> bool:
    return lang_code in INDIAN_LANGUAGES


def get_language_name(lang_code: str) -> str:
    if lang_code in INDIAN_LANGUAGES:
        return INDIAN_LANGUAGES[lang_code]
    try:
        import langdetect
        return lang_code
    except Exception:
        return lang_code


def translate_text(text: str, target_lang: str = "en") -> str:
    if not isinstance(text, str) or not text.strip():
        return ""
    try:
        from transformers import pipeline
        from compute.gpu_manager import GPUManager, is_cuda
        mgr = GPUManager()
        device = mgr.device if is_cuda() else -1
        translator = pipeline(
            "translation",
            model="Helsinki-NLP/opus-mt-mul-en",
            device=device,
        )
        result = translator(text[:512], max_length=512)
        return result[0]["translation_text"]
    except ImportError:
        logger.warning("transformers not available for translation")
        return text
    except Exception as e:
        logger.warning("Translation failed: %s", e)
        return text
