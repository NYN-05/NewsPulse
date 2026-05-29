import logging
from typing import Optional

logger = logging.getLogger(__name__)

DEVICE: Optional[str] = None
_HAS_CUDA: bool = False
_HAS_SENTENCE_TRANSFORMERS: bool = False


def detect_cuda() -> bool:
    global _HAS_CUDA
    try:
        import torch
        _HAS_CUDA = torch.cuda.is_available()
        if _HAS_CUDA:
            logger.info("CUDA available: %s (device count: %d)", torch.cuda.get_device_name(0), torch.cuda.device_count())
        else:
            logger.info("CUDA not available, using CPU")
        return _HAS_CUDA
    except Exception as e:
        logger.warning("CUDA detection failed: %s", e)
        _HAS_CUDA = False
        return False


def get_device() -> str:
    global DEVICE
    if DEVICE is not None:
        return DEVICE
    if detect_cuda():
        DEVICE = "cuda"
    else:
        DEVICE = "cpu"
    logger.info("Using device: %s", DEVICE)
    return DEVICE


def is_cuda() -> bool:
    return get_device() == "cuda"


def has_sentence_transformers() -> bool:
    global _HAS_SENTENCE_TRANSFORMERS
    if _HAS_SENTENCE_TRANSFORMERS:
        return True
    try:
        import sentence_transformers
        _HAS_SENTENCE_TRANSFORMERS = True
        return True
    except ImportError:
        return False


class GPUManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.device = get_device()
        self.cuda = is_cuda() if callable(is_cuda) else bool(is_cuda)
        self._pipelines = {}

    @property
    def torch_device(self):
        import torch
        return torch.device(self.device)

    def get_pipeline(self, task: str, model_name: str = None):
        _model_map = {
            "sentiment": ("sentiment-analysis", "distilbert-base-uncased-finetuned-sst-2-english"),
            "ner": ("ner", "dslim/bert-base-NER"),
            "summarization": ("summarization", "t5-small"),
            "zero-shot": ("zero-shot-classification", "facebook/bart-large-mnli"),
        }
        hf_task, default_model = _model_map.get(task, (task, None))
        cache_key = f"{hf_task}:{model_name or default_model}"
        if cache_key in self._pipelines:
            return self._pipelines[cache_key]
        from transformers import pipeline
        if model_name is None:
            model_name = default_model
        if model_name is None:
            raise ValueError(f"No default model for task: {task}")
        logger.info("Loading %s pipeline (%s) on %s...", hf_task, model_name, self.device)
        pipe = pipeline(hf_task, model=model_name, device=self.device)
        self._pipelines[cache_key] = pipe
        return pipe

    def clear_pipelines(self):
        cached = list(self._pipelines.keys())
        self._pipelines.clear()
        import gc
        gc.collect()
        if self.cuda:
            try:
                import torch
                torch.cuda.empty_cache()
                logger.info("GPU cache emptied after clearing %d pipelines", len(cached))
            except Exception:
                pass
        if cached:
            logger.info("Cleared %d cached pipelines from GPUManager", len(cached))


device = get_device()
_IS_CUDA = is_cuda()  # cache result, use callable check in __init__
DEVICE = device
