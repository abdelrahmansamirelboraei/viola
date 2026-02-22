from __future__ import annotations


def start_web_chat(*args, **kwargs) -> None:
    """
    Stable web adapter entry point.
    Accepts any arguments from CLI without breaking.
    """

    from viola.web.web_app import run_web

    # Default host/port
    host = "127.0.0.1"
    port = 8000

    # Try to extract host/port if passed
    if 'host' in kwargs:
        host = kwargs.get('host', host)
    if 'port' in kwargs:
        port = kwargs.get('port', port)

    run_web(host=host, port=port)


# Optional alias
def run_web_chat(*args, **kwargs):
    start_web_chat(*args, **kwargs)
