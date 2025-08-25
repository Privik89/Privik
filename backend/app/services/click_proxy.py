from urllib.parse import quote_plus


def build_proxy_url(original_url: str) -> str:
    """Return a placeholder proxy URL that would isolate the click via a secure gateway.

    In the MVP this just encodes and forwards. Later, this will point to our analysis
    service which performs screenshotting, DOM inspection, and login-page detection.
    """
    return f"https://proxy.example/visit?u={quote_plus(original_url)}"


