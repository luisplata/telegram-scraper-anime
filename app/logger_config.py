import logging


def configure_logging():
    """Configure basic logging for the app if not already configured.

    This uses a simple format and INFO level so users see progress by default.
    Calling it multiple times is safe because basicConfig has no effect after
    the first call if handlers are already configured.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    )


# Auto-configure on import for convenience when running scripts.
configure_logging()
