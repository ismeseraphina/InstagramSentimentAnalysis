import csv
import json
import re
from pathlib import Path
_PATTERN = re.compile(r"[a-z0-9._]{1,30}\Z", re.ASCII)

def normalize_username(value):
    if not isinstance(value, str):
        raise ValueError("Username must be a string")
    value = value.strip().removeprefix("@").lower()
    if not _PATTERN.fullmatch(value):
        raise ValueError("Invalid username syntax")
    return value


def _users(values):
    if isinstance(values, (str, bytes, dict)):
        raise ValueError("Expected an iterable of username strings")
    try:
        return {normalize_username(value) for value in values}
    except TypeError as exc:
        raise ValueError("Expected an iterable of username strings") from exc
