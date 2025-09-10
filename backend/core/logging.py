import logging


def setup_logging(level: int = logging.INFO):
    """Basic logging setup for the gateway. Call once during startup."""
    root = logging.getLogger()
    if root.handlers:
        # already configured
        return
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(level)


# convenience
logger = logging.getLogger("signally.gateway")

