import json
import re
from pathlib import Path

input_paths = [
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_cleaned.json"),
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_postpaid_cleaned.json"),
]

def extract_price(text):
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", str(text))
    return float(match.group(1)) if match else None

def extract_currency(text):
    if not text:
        return None
    if re.search(r"\b(PKR|Rs\.?|Rs)\b", str(text), flags=re.IGNORECASE):
        return "PKR"
    return None

def extract_billing_cycle_days(text):
    if not text:
        return None

    lowered = str(text).lower()

    if re.search(r"\bmonthly\b|/\s*month\b|per\s*month\b", lowered):
        return 30
    if re.search(r"\bweekly\b|/\s*week\b|per\s*week\b", lowered):
        return 7
    if re.search(r"\bdaily\b|/\s*day\b|per\s*day\b", lowered):
        return 1
    if re.search(r"\bone\s*time\b", lowered):
        return 1
    if re.search(r"\bper\s*message\b|/\s*message\b|per\s*sms\b|/\s*sms\b", lowered):
        return 1
    if re.search(r"\bper\s*minute\b|/\s*min\b|/\s*minutes?\b", lowered):
        return 1

    return None

def pick_price_source(record):
    price_sources = [
        record.get("price"),
        record.get("terms_and_conditions"),
        record.get("more_detail_url"),
    ]

    more_details = record.get("more_details")
    if isinstance(more_details, dict):
        for value in more_details.values():
            price_sources.append(value)

    for source in price_sources:
        if isinstance(source, str) and source.strip():
            return source
        if isinstance(source, (int, float)):
            return source

    return None

def normalize_record(record):
    source = pick_price_source(record)

    record["price"] = extract_price(source)
    record["currency"] = extract_currency(source)
    record["billing_cycle"] = extract_billing_cycle_days(source)

    if record["currency"] is None and isinstance(source, str):
        record["currency"] = "PKR" if "rs" in source.lower() or "pkr" in source.lower() else None

    return record

for path in input_paths:
    with path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    updated_records = [normalize_record(record) for record in records]

    with path.open("w", encoding="utf-8") as file:
        json.dump(updated_records, file, indent=2, ensure_ascii=False)

    print(f"Updated: {path}")