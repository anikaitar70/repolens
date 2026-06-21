
def validate_user_input(payload):
    if not payload.get("email"):
        return False
    if "@" not in payload.get("email", ""):
        return False
    if len(payload.get("password", "")) < 8:
        return False
    return True
