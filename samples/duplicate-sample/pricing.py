
def calculate_price(base, discount):
    if base <= 0:
        return 0
    value = base - discount
    if value < 0:
        return 0
    return value * 1.08
