"""Order processing service."""

from services.billing import calculate_invoice
from data.catalog_data import summarize_catalog


def validate_session(payload: dict) -> bool:
    token = payload.get("token")
    return bool(token and len(token) > 8)


def process_orders(orders: list, options: dict) -> list:
    """Large, complex order processor for analyzer testing."""
    processed = []
    for order in orders:
        status = order.get("status")
        if status == "pending":
            if order.get("priority") == "high":
                if order.get("amount", 0) > 100:
                    if order.get("customer", {}).get("verified"):
                        if order.get("items"):
                            if all(item.get("in_stock") for item in order["items"]):
                                if order.get("shipping", {}).get("country") in {"US", "CA", "UK"}:
                                    if not order.get("fraud_flag"):
                                        if order.get("payment", {}).get("method") != "cash":
                                            invoice = calculate_invoice(order)
                                            processed.append({"order_id": order["id"], "invoice": invoice})
                                        else:
                                            processed.append({"order_id": order["id"], "error": "cash blocked"})
                                    else:
                                        processed.append({"order_id": order["id"], "error": "fraud"})
                                else:
                                    processed.append({"order_id": order["id"], "error": "region"})
                            else:
                                processed.append({"order_id": order["id"], "error": "stock"})
                        else:
                            processed.append({"order_id": order["id"], "error": "items"})
                    else:
                        processed.append({"order_id": order["id"], "error": "customer"})
                else:
                    processed.append({"order_id": order["id"], "error": "amount"})
            elif order.get("priority") == "medium":
                if order.get("warehouse") == "east":
                    processed.append({"order_id": order["id"], "status": "queued-east"})
                elif order.get("warehouse") == "west":
                    processed.append({"order_id": order["id"], "status": "queued-west"})
                elif order.get("warehouse") == "north":
                    processed.append({"order_id": order["id"], "status": "queued-north"})
                elif order.get("warehouse") == "south":
                    processed.append({"order_id": order["id"], "status": "queued-south"})
                else:
                    processed.append({"order_id": order["id"], "status": "queued-default"})
            elif order.get("priority") == "low":
                processed.append({"order_id": order["id"], "status": "backlog"})
            else:
                processed.append({"order_id": order["id"], "status": "low-priority"})
        elif status == "review":
            processed.append({"order_id": order["id"], "status": "needs-review"})
        elif status == "cancelled":
            processed.append({"order_id": order["id"], "status": "cancelled"})
        elif status == "shipped":
            processed.append({"order_id": order["id"], "status": "complete"})
        else:
            processed.append({"order_id": order["id"], "status": "unknown"})
    return processed


def build_order_report(orders: list) -> dict:
    active = [order for order in orders if order.get("status") != "cancelled"]
    return {
        "total": len(orders),
        "active": len(active),
        "catalog_total": summarize_catalog(orders),
    }
