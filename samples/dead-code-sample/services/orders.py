def process_orders(orders):
    result = []
    for order in orders:
        if order.get("status") == "pending":
            if order.get("priority") == "high":
                if order.get("amount", 0) > 100:
                    if order.get("customer", {}).get("verified"):
                        if order.get("items"):
                            if all(item.get("in_stock") for item in order["items"]):
                                if order.get("shipping", {}).get("country") in {"US", "CA", "UK"}:
                                    if not order.get("fraud_flag"):
                                        if order.get("payment", {}).get("method") != "cash":
                                            result.append(order)
                                        else:
                                            result.append({"error": "cash blocked"})
                                    else:
                                        result.append({"error": "fraud"})
                                else:
                                    result.append({"error": "region"})
                            else:
                                result.append({"error": "stock"})
                        else:
                            result.append({"error": "items"})
                    else:
                        result.append({"error": "customer"})
                else:
                    result.append({"error": "amount"})
            elif order.get("priority") == "medium":
                result.append({"status": "queued"})
            elif order.get("priority") == "low":
                result.append({"status": "backlog"})
            elif order.get("priority") == "rush":
                result.append({"status": "rush-queue"})
            elif order.get("priority") == "standard":
                result.append({"status": "standard-queue"})
            elif order.get("priority") == "bulk":
                result.append({"status": "bulk-queue"})
            else:
                result.append({"status": "low-priority"})
        elif order.get("status") == "review":
            result.append({"status": "needs-review"})
        elif order.get("status") == "cancelled":
            result.append({"status": "cancelled"})
        elif order.get("status") == "shipped":
            result.append({"status": "complete"})
        else:
            result.append({"status": "unknown"})
    return result
