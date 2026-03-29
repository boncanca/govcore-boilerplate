import logging
from functools import wraps

audit_logger = logging.getLogger("audit")

def audit_action(action: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            user = kwargs.get("user")
            audit_logger.info(
                "action=%s user=%s",
                action,
                getattr(user, "id", "system"),
            )
            return result
        return wrapper
    return decorator
