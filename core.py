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

def _json_values(data):
    if isinstance(data, dict):
        keys = [k for k in ("usernames", "relationships_following", "relationships_followers") if k in data]
        if len(keys) != 1:
            raise ValueError("JSON object must have exactly one supported list key")
        data = data[keys[0]]
    if not isinstance(data, list):
        raise ValueError("Expected a JSON list")
    if all(isinstance(item, str) for item in data):
        return data
    result = []
    for item in data:
        if not isinstance(item, dict) or not isinstance(item.get("string_list_data"), list) or not item["string_list_data"]:
            raise ValueError("Expected non-empty string_list_data objects; mixed formats are not supported")
        for record in item["string_list_data"]:
            if not isinstance(record, dict) or not isinstance(record.get("value"), str):
                raise ValueError("Expected a string value in string_list_data")
            result.append(record["value"])
    return result
