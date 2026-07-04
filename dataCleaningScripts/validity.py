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


def normalize_text(value):
    if value is None:
        return None

    text = str(value).replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return None

    if text.lower() in {"n/a", "na", "none", "null", "-"}:
        return None

    return text


def normalize_key(key):
    text = str(key).lower()
    return re.sub(r"[^a-z0-9]+", "", text)


# -------------------------------------------------------
# Validity extraction
# -------------------------------------------------------

def score_validity_text(text):
    if not text:
        return -1

    lower = text.lower()
    score = 0

    if "validity" in lower:
        score += 5

    if re.search(r"\b(day|days|week|weeks|month|months|hour|hours|daily|weekly|monthly)\b", lower):
        score += 4

    if re.search(r"\b\d+\s*(day|days|week|weeks|month|months|hour|hours)\b", lower):
        score += 4

    if len(text) > 120:
        score -= 3

    if "terms and conditions" in lower:
        score -= 2

    return score


def extract_validity_pattern(text):
    if not text:
        return None

    text = normalize_text(text)

    if not text:
        return None

    if len(text) <= 80 and score_validity_text(text) >= 6:
        return text

    patterns = [
        r"(?:\d+\s*(?:day|days|week|weeks|month|months|hour|hours)(?:\s*/\s*)?)+",
        r"\b(?:daily|weekly|monthly)\b",
    ]

    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            return m.group(0).strip()

    return None


def extract_validity_from_more_details(more_details):
    if not isinstance(more_details, dict):
        return None

    candidates = []

    for key, value in more_details.items():
        key_n = normalize_key(key)
        value_t = normalize_text(value)

        if not value_t:
            continue

        candidate = extract_validity_pattern(value_t)

        if not candidate:
            continue

        score = score_validity_text(candidate)

        if "validity" in key_n:
            score += 6
        elif key_n in {"duration", "period"}:
            score += 3

        candidates.append((score, candidate))

    if not candidates:
        return None

    candidates.sort(reverse=True)

    return candidates[0][1]


def extract_validity_from_terms(terms_text):
    terms_text = normalize_text(terms_text)

    if not terms_text:
        return None

    for line in re.split(r"[\n\.]", terms_text):
        line = normalize_text(line)

        if not line:
            continue

        if "validity" in line.lower():
            candidate = extract_validity_pattern(line)

            if candidate:
                return candidate

    return extract_validity_pattern(terms_text)


def pick_best_validity(record):
    existing = extract_validity_pattern(record.get("validity"))

    if existing:
        return existing

    md = extract_validity_from_more_details(record.get("more_details"))

    if md:
        return md

    tc = extract_validity_from_terms(record.get("terms_and_conditions"))

    if tc:
        return tc

    return None


# -------------------------------------------------------
# Convert validity to standardized days
# -------------------------------------------------------

def validity_to_days(validity):
    """
    Converts validity into standardized days.

    Examples
    --------
    Daily -> [1]
    Weekly -> [7]
    Monthly -> [30]
    7 Days -> [7]
    2 Weeks -> [14]
    3 Months -> [90]
    24 Hours -> [1]
    48 Hours -> [2]
    1Day/7 Days/30 Days -> [1,7,30]
    """

    validity = normalize_text(validity)

    if not validity:
        return None

    text = validity.lower()

    days = []

    # -------- numeric values --------

    matches = re.findall(
        r"(\d+)\s*(day|days|week|weeks|month|months|hour|hours)",
        text,
        flags=re.IGNORECASE,
    )

    for number, unit in matches:

        number = int(number)

        unit = unit.lower()

        if "day" in unit:
            days.append(number)

        elif "week" in unit:
            days.append(number * 7)

        elif "month" in unit:
            days.append(number * 30)

        elif "hour" in unit:
            days.append(max(1, number // 24))

    # -------- textual validity --------

    if "daily" in text:
        days.append(1)

    if "weekly" in text:
        days.append(7)

    if "monthly" in text:
        days.append(30)

    # remove duplicates while preserving order

    seen = set()
    result = []

    for d in days:
        if d not in seen:
            seen.add(d)
            result.append(d)

    return result or None


# -------------------------------------------------------
# Matching
# -------------------------------------------------------

def record_key(record):
    return (
        normalize_text(record.get("plan_name")) or "",
        normalize_text(record.get("more_detail_url")) or "",
    )


def update_cleaned_validity(source_records, target_records):
    target_map = {record_key(r): r for r in target_records}

    updated = 0
    missing = 0

    for src in source_records:

        key = record_key(src)

        target = target_map.get(key)

        if target is None:
            plan = normalize_text(src.get("plan_name")) or ""

            matches = [
                r
                for r in target_records
                if (normalize_text(r.get("plan_name")) or "") == plan
            ]

            target = matches[0] if matches else None

        if target is None:
            missing += 1
            continue

        validity = pick_best_validity(src)

        target["validity"] = validity
        target["validity_days"] = validity_to_days(validity)

        updated += 1

    return updated, missing


# -------------------------------------------------------
# Main
# -------------------------------------------------------

for input_path, output_path in zip(INPUT_PATHS, OUTPUT_PATHS):

    with input_path.open("r", encoding="utf-8") as f:
        source_records = json.load(f)

    with output_path.open("r", encoding="utf-8") as f:
        target_records = json.load(f)

    updated_count, missing_count = update_cleaned_validity(
        source_records,
        target_records,
    )

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            target_records,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Updated: {output_path}")
    print(f"Matched: {updated_count}")
    print(f"Missing: {missing_count}")