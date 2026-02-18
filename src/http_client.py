import time
import requests


def request_with_retry(method: str, url: str, max_retries: int = 2, retry_delay: int = 3, **kwargs) -> requests.Response:
    """HTTP 요청 + 네트워크 오류 시 재시도. 응답은 그대로 반환."""
    kwargs.setdefault("timeout", 30)
    last_error = None
    for attempt in range(1 + max_retries):
        try:
            return requests.request(method, url, **kwargs)
        except (requests.ConnectionError, requests.Timeout) as e:
            last_error = e
            if attempt < max_retries:
                print(f"  [RETRY] {attempt + 1}/{max_retries} - {type(e).__name__}")
                time.sleep(retry_delay)
    raise last_error
