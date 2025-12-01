import logfire

from app.core.config import settings

_configured = False


def setup_logging():
    """Configure logfire once."""
    global _configured
    if _configured:
        return logfire
    logfire.configure(
        service_name=settings.LOGFIRE_SERVICE_NAME,
        send_to_logfire=settings.LOGFIRE_SEND_TO_LOGFIRE,
    )
    _configured = True
    return logfire


def get_logger(name: str):
    """
    Get a logfire logger-like object; tag with the logger name for context.
    logfire exposes module-level methods, so we use with_tags instead of get_logger.
    """
    lf = setup_logging()
    # with_tags expects hashable entries; use a string tag instead of a dict.
    return lf.with_tags(f"logger:{name}")
