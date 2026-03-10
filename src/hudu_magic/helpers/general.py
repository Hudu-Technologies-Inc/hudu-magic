def strip_string(value: str, remove: list[str]) -> str:
    for item in remove:
        value = value.replace(item, "")
    return value