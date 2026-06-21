"""Fulfillment service."""

from auth.security import check


def schedule_delivery(order: dict) -> float:
    if check({"token": order.get("session_token", "")}):
        return 12.5
    return 99.0
