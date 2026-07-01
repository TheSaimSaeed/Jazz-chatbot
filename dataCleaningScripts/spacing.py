import json
import re
from pathlib import Path

input_paths = [
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_cleaned.json"),
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_postpaid_cleaned.json"),
]


def normalize_whitespace(text):
    if text is None:
        return None

    if not isinstance(text, str):
        return text

    text = text.replace("\u00a0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            lines.append("")
            continue

        line = re.sub(r"[ \t]+", " ", line)
        line = re.sub(r"\s+([,.;:!?])", r"\1", line)
        line = re.sub(r"([({\[]])\s+", r"\1", line)
        line = re.sub(r"\s+([)\]}])", r"\1", line)
        line = re.sub(r"\s*-\s*", " - ", line)
        lines.append(line)

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def normalize_plan_name(text):
    text = normalize_whitespace(text)
    if not text:
        return text

    return re.sub(r"\s{2,}", " ", text)


def extract_price(text):
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def extract_currency(text):
    if not text:
        return None
    if re.search(r"\b(?:PKR|Rs\.?|Rs)\b", text, flags=re.IGNORECASE):
        return "PKR"
    return None


def extract_billing_cycle(text):
    if not text:
        return None

    lowered = text.lower()
    if re.search(r"\bmonthly\b|/\s*month\b|per\s*month\b", lowered):
        return "monthly"
    if re.search(r"\bweekly\b|/\s*week\b|per\s*week\b", lowered):
        return "weekly"
    if re.search(r"\bdaily\b|/\s*day\b|per\s*day\b", lowered):
        return "daily"
    if re.search(r"\bper\s*message\b|\bper\s*sms\b|/\s*message\b|/\s*sms\b", lowered):
        return "per_message"
    if re.search(r"\bper\s*minute\b|/\s*min\b|/\s*minutes?\b", lowered):
        return "per_minute"
    if re.search(r"\bone\s*time\b", lowered):
        return "one_time"
    return None


def normalize_price_field(value):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return {
            "price": value,
            "currency": "PKR",
            "billing_cycle": None,
        }

    if not isinstance(value, str):
        return value

    price = extract_price(value)
    currency = extract_currency(value)
    billing_cycle = extract_billing_cycle(value)

    if price is None and currency is None and billing_cycle is None:
        return normalize_whitespace(value)

    return {
        "price": price,
        "currency": currency,
        "billing_cycle": billing_cycle,
    }


def normalize_record(record):
    cleaned = {}

    for key, value in record.items():
        if key == "price":
            price_info = normalize_price_field(value)
            if isinstance(price_info, dict):
                cleaned["price"] = price_info["price"]
                cleaned["currency"] = price_info["currency"]
                cleaned["billing_cycle"] = price_info["billing_cycle"]
            else:
                cleaned["price"] = price_info
            continue

        if isinstance(value, str):
            cleaned[key] = normalize_plan_name(value) if key == "plan_name" else normalize_whitespace(value)
        elif isinstance(value, dict):
            cleaned[key] = {
                sub_key: normalize_whitespace(sub_value) if isinstance(sub_value, str) else sub_value
                for sub_key, sub_value in value.items()
            }
        elif isinstance(value, list):
            cleaned[key] = [
                normalize_whitespace(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            cleaned[key] = value

    if "currency" not in cleaned:
        cleaned["currency"] = None
    if "billing_cycle" not in cleaned:
        cleaned["billing_cycle"] = None

    return cleaned


for path in input_paths:
    with path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    normalized_records = [normalize_record(record) for record in records]

    with path.open("w", encoding="utf-8") as file:
        json.dump(normalized_records, file, indent=2, ensure_ascii=False)

    print(f"Saved normalized data to: {path}")
