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

def load_users(path):
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        if path.suffix.lower() == ".json":
            values = _json_values(json.load(stream))
        elif path.suffix.lower() == ".txt":
            values = [line.strip() for line in stream if line.strip()]
        elif path.suffix.lower() == ".csv":
            try:
                reader = csv.reader(stream, strict=True)
                header = next(reader, None)
                if not header or header.count("username") != 1 or len(set(header)) != len(header):
                    raise ValueError("CSV requires unique headers including 'username'")
                column, values = header.index("username"), []
                for row in reader:
                    if len(row) != len(header):
                        raise ValueError(f"Wrong cell count near CSV line {reader.line_num}")
                    values.append(row[column])
            except csv.Error as exc:
                raise ValueError("Malformed CSV") from exc
        else:
            raise ValueError("Supported extensions: .json, .csv, .txt")
    return _users(values)

def analyze(followers, following):
    followers, following = _users(followers), _users(following)
    return {"counts": {"followers": len(followers), "following": len(following), "mutuals": len(followers & following)},
            "not_following_back": sorted(following - followers),
            "fans": sorted(followers - following), "mutuals": sorted(followers & following)}


def compare_snapshots(before, after):
    before, after = _users(before), _users(after)
    return {"added": sorted(after - before), "removed": sorted(before - after), "unchanged_count": len(before & after)}
