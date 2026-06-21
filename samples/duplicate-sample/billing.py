
def compute_cost(amount, reduction):
    if amount <= 0:
        return 0
    result = amount - reduction
    if result < 0:
        return 0
    return result * 1.08
