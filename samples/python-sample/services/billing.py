"""Billing service."""

from services.fulfillment import schedule_delivery


def calculate_invoice(order: dict) -> dict:
    subtotal = sum(item.get("price", 0) for item in order.get("items", []))
    tax = subtotal * 0.08
    shipping = schedule_delivery(order)
    return {"subtotal": subtotal, "tax": tax, "shipping": shipping, "total": subtotal + tax + shipping}
