import logfire
from app.core.config import settings


def setup_logfire():
    logfire.configure(
        token=settings.logfire_token,
        send_to_logfire=(settings.logfire_token != "dummy_logfire_token"),
        service_name="ai-platform",
    )
