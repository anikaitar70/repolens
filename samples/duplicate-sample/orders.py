
def process_order(order):
    if order.get("status") != "pending":
        return 0
    amount = order.get("amount", 0)
    tax = order.get("tax", 0)
    total = amount + tax
    if total > 100:
        return total * 0.9
    return total
