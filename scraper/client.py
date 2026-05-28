import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config.settings import get
import logging

logger = logging.getLogger(__name__)


def build_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=get("scraper.retry_attempts", 3),
        backoff_factor=get("scraper.retry_backoff", 1.0),
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": get("scraper.user_agent", "")})
    return session


_global_session: requests.Session = None


def get_session() -> requests.Session:
    global _global_session
    if _global_session is None:
        _global_session = build_session()
    return _global_session


def reset_session():
    global _global_session
    if _global_session is not None:
        _global_session.close()
    _global_session = None


def fetch(url: str, timeout: int = None) -> requests.Response:
    if timeout is None:
        timeout = get("scraper.timeout", 15)
    session = get_session()
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp
