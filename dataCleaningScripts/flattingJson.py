import json
import re
from pathlib import Path

INPUT_PATHS = [
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_cleaned.json"),
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_postpaid_cleaned.json"),
]


def normalize_key(key, fallback="field"):
    text = str(key).replace("\u00a0", " ").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or fallback


def set_value(result, key, value):
    if not key:
        return
    if key not in result or result[key] in (None, "", [], {}):
        result[key] = value


def flatten_value(prefix, value, result):
    if not prefix:
        return

    if isinstance(value, dict):
        if not value:
            set_value(result, prefix, None)
            return

        for child_key, child_value in value.items():
            child_name = normalize_key(child_key)
            next_prefix = f"{prefix}_{child_name}" if prefix else child_name
            flatten_value(next_prefix, child_value, result)
        return

    if isinstance(value, list):
        if not value:
            set_value(result, prefix, [])
            return

        if all(not isinstance(item, (dict, list)) for item in value):
            set_value(result, prefix, value)
            return

        for index, item in enumerate(value):
            flatten_value(f"{prefix}_{index}", item, result)
        return

    set_value(result, prefix, value)


def flatten_record(record):
    flat = {}

    for key, value in record.items():
        if key == "more_details":
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    nested_name = normalize_key(nested_key)
                    flatten_value(nested_name, nested_value, flat)
            continue

        flat_key = normalize_key(key)
        flatten_value(flat_key, value, flat)

    return flat


for input_path in INPUT_PATHS:
    with input_path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    flattened_records = [flatten_record(record) for record in records]

    with input_path.open("w", encoding="utf-8") as file:
        json.dump(flattened_records, file, indent=2, ensure_ascii=False)

    print(f"Flattened: {input_path}")