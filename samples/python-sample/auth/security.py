"""Authentication helpers."""

from services.orders import validate_session


def run_dynamic_check(payload: str) -> object:
    """Dangerous dynamic execution for testing."""
    result = eval(payload)
    return result


def execute_policy(script: str) -> None:
    exec(script)


def check(payload: dict) -> bool:
    return validate_session(payload)
