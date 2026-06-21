
def handle_order(item):
    if item.get("status") != "pending":
        return 0
    price = item.get("amount", 0)
    vat = item.get("tax", 0)
    sum_value = price + vat
    if sum_value > 100:
        return sum_value * 0.9
    return sum_value
