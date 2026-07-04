import json
import re
from pathlib import Path

INPUT_PATHS = [
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers.json"),
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_postpaid.json"),
]

OUTPUT_PATHS = [
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_cleaned.json"),
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_postpaid_cleaned.json"),
]


PRICE_HINT_PATTERNS = [
    r"rs\.?\s*\d+(?:,\d{3})*(?:\.\d+)?",
    r"pkr\s*\d+(?:,\d{3})*(?:\.\d+)?",
    r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:rs\.?|pkr)",
    r"\d+(?:\.\d+)?\s*/\s*(?:month|monthly|week|weekly|day|daily|min|minute|message|sms|mb|gb)",
    r"(?:month|monthly|week|weekly|day|daily|min|minute|message|sms|mb|gb)\s*[:\-]?\s*rs\.?\s*\d+(?:,\d{3})*(?:\.\d+)?",
]

EXCLUDE_NOISE_PATTERNS = [
    r"^\s*\d+\.\s*",          # list numbering like "1. Upon dialing..."
    r"^\s*\d+\s*-\s*",        # headings like "1 - month"
    r"mcc[- ]?mnc",
    r"terms and conditions",
    r"sharing rules",
    r"available\s+\*?\d+#",
]


def normalize_text(value):
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_noise_text(text):
    lowered = text.lower()
    return any(re.search(pattern, lowered, flags=re.IGNORECASE) for pattern in EXCLUDE_NOISE_PATTERNS)


def extract_currency(text):
    if not text:
        return None
    if re.search(r"\b(PKR|Rs\.?|Rs)\b", text, flags=re.IGNORECASE):
        return "PKR"
    return None


def extract_billing_cycle_days(text):
    if not text:
        return None

    lowered = text.lower()

    if re.search(r"\bmonthly\b|/\s*month\b|per\s*month\b", lowered):
        return 30
    if re.search(r"\bweekly\b|/\s*week\b|per\s*week\b", lowered):
        return 7
    if re.search(r"\bdaily\b|/\s*day\b|per\s*day\b", lowered):
        return 1
    if re.search(r"\bone\s*time\b|one-time\b", lowered):
        return 1
    if re.search(r"\bper\s*message\b|/\s*message\b|per\s*sms\b|/\s*sms\b", lowered):
        return 1
    if re.search(r"\bper\s*minute\b|/\s*min\b|/\s*minute\b|/\s*minutes\b", lowered):
        return 1

    return None


def normalize_numeric_price(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = normalize_text(value)
    if not text:
        return None

    if is_noise_text(text):
        return None

    compact = text.replace(",", "")
    match = re.search(r"(?:rs\.?|pkr)?\s*(\d+(?:\.\d+)?)", compact, flags=re.IGNORECASE)
    if not match:
        return None

    return float(match.group(1))


def get_price_candidates(record):
    candidates = []

    for key in ("price", "terms_and_conditions", "more_detail_url"):
        value = record.get(key)
        if value not in (None, "", [], {}):
            candidates.append((key, value))

    more_details = record.get("more_details")
    if isinstance(more_details, dict):
        for key, value in more_details.items():
            candidates.append((f"more_details.{key}", value))

    return candidates


def extract_price_from_text(text):
    text = normalize_text(text)
    if not text or is_noise_text(text):
        return None

    compact = text.replace("\u00a0", " ")
    compact = re.sub(r"\s+", " ", compact)

    for pattern in PRICE_HINT_PATTERNS:
        match = re.search(pattern, compact, flags=re.IGNORECASE)
        if match:
            price_text = match.group(0)
            price = normalize_numeric_price(price_text)
            if price is not None:
                return price

    return None


def pick_best_price(record):
    current_price = normalize_numeric_price(record.get("price"))
    if current_price is not None:
        return current_price

    candidates = get_price_candidates(record)

    best_price = None
    best_rank = -1

    for source_name, source_value in candidates:
        text = normalize_text(source_value)
        if not text:
            continue

        if source_name == "price":
            price = normalize_numeric_price(text)
            if price is not None:
                return price

        if is_noise_text(text):
            continue

        price = extract_price_from_text(text)
        if price is None:
            continue

        rank = 0
        if source_name.startswith("more_details"):
            rank = 2
        elif source_name == "terms_and_conditions":
            rank = 1
        elif source_name == "more_detail_url":
            rank = -1

        if rank > best_rank:
            best_rank = rank
            best_price = price

    return best_price


def normalize_record(record):
    price = pick_best_price(record)
    record["price"] = price

    source_text = normalize_text(record.get("terms_and_conditions")) or normalize_text(record.get("price"))
    if not source_text:
        more_details = record.get("more_details")
        if isinstance(more_details, dict):
            source_text = " ".join(normalize_text(v) for v in more_details.values() if normalize_text(v))

    if source_text:
        record["currency"] = extract_currency(source_text)
        record["billing_cycle"] = extract_billing_cycle_days(source_text)
    else:
        record["currency"] = record.get("currency")
        record["billing_cycle"] = record.get("billing_cycle")

    return record


for input_path, output_path in zip(INPUT_PATHS, OUTPUT_PATHS):
    with input_path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    updated_records = [normalize_record(record) for record in records]

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(updated_records, file, indent=2, ensure_ascii=False)

    print(f"Updated: {output_path}")