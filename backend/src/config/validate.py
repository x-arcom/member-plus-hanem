from typing import List


def validate_required_values(values: dict) -> List[str]:
    missing = [name for name, value in values.items() if not value]
    return missing


def ensure_config(values: dict) -> None:
    missing = validate_required_values(values)
    if missing:
        raise RuntimeError(f"Missing required configuration values: {', '.join(missing)}")
