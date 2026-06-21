
def validate_admin_input(data):
    if not data.get("email"):
        return False
    if "@" not in data.get("email", ""):
        return False
    if len(data.get("password", "")) < 8:
        return False
    return True
