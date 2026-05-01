"""Input validation helpers."""


def validate_required(data: dict, fields: list[str]) -> str | None:
    """Returns error message string if any required field is missing, else None."""
    if not data:
        return "Request body is empty"
    missing = [f for f in fields if not data.get(f)]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    return None
