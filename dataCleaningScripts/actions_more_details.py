import json
import re
from pathlib import Path

input_paths = [
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_cleaned.json"),
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_postpaid_cleaned.json"),
]

def normalize_text(value):
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    value = value.replace("\u00a0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value or None

def clean_key(value):
    text = normalize_text(value)
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]+", "", text.lower())

def extract_dial_code(text):
    if not text:
        return None
    match = re.search(r"\*[\d*#]+#", str(text))
    return match.group(0) if match else None

def extract_number(text):
    if not text:
        return None
    match = re.search(r"(\d{3,8})", str(text))
    return match.group(1) if match else None

def extract_code_value(text, kind):
    if not text:
        return None

    normalized = normalize_text(text)
    dial_code = extract_dial_code(normalized)
    if dial_code:
        return dial_code

    if kind == "subscription" and re.search(r"\bsub\b", normalized, flags=re.IGNORECASE):
        return "SUB"

    if kind == "unsubscribe" and re.search(r"\bunsub\b", normalized, flags=re.IGNORECASE):
        return "UNSUB"

    return normalized

def is_price_key(key_norm):
    return any(token in key_norm for token in [
        "price",
        "fee",
        "charge",
        "amount",
        "required",
        "payment",
        "subscriptionfee",
        "recharge",
    ])

def is_subscription_key(key_norm):
    return key_norm in {
        "subscriptioncode",
        "subscriptionstring",
        "subscribe",
        "subscription",
        "subcode",
    } or key_norm.startswith("subscriptioncode") or key_norm.startswith("subscriptionstring")

def is_unsubscription_key(key_norm):
    return key_norm in {
        "unsubscribe",
        "unsub",
        "unsubscribecode",
        "unsubscription",
        "unsubscriptioncode",
    } or key_norm.startswith("unsubscribecode") or key_norm.startswith("unsubscriptioncode")

def is_dial_key(key_norm):
    return key_norm in {
        "dial",
        "dialcode",
        "ussd",
        "statuscode",
        "bundleinformationcode",
        "informationcode",
        "infocode",
        "helpcode",
    } or "dial" in key_norm or "ussd" in key_norm

def extract_actionable_fields(more_details):
    fields = {
        "subscription_code": None,
        "subscription_number": None,
        "unsubscribe_code": None,
        "unsubscribe_number": None,
        "dial_code": None,
    }

    if not isinstance(more_details, dict):
        return fields

    for key, raw_value in more_details.items():
        key_norm = clean_key(key)
        value = normalize_text(raw_value)
        if not value:
            continue

        if is_price_key(key_norm):
            continue

        if is_unsubscription_key(key_norm):
            if fields["unsubscribe_code"] is None:
                fields["unsubscribe_code"] = extract_code_value(value, "unsubscribe")
            if fields["unsubscribe_number"] is None:
                number = extract_number(value)
                if number is not None:
                    fields["unsubscribe_number"] = number
            continue

        if is_subscription_key(key_norm):
            if fields["subscription_code"] is None:
                fields["subscription_code"] = extract_code_value(value, "subscription")
            if fields["subscription_number"] is None:
                number = extract_number(value)
                if number is not None:
                    fields["subscription_number"] = number
            if fields["dial_code"] is None:
                fields["dial_code"] = extract_dial_code(value)
            continue

        if is_dial_key(key_norm) and fields["dial_code"] is None:
            fields["dial_code"] = extract_dial_code(value) or value

    if fields["dial_code"] is None:
        fields["dial_code"] = extract_dial_code(fields["subscription_code"] or "")

    if fields["subscription_number"] is None and fields["subscription_code"]:
        fields["subscription_number"] = extract_number(fields["subscription_code"])

    if fields["unsubscribe_number"] is None and fields["unsubscribe_code"]:
        fields["unsubscribe_number"] = extract_number(fields["unsubscribe_code"])

    return fields

for input_path in input_paths:
    with input_path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    for record in records:
        more_details = record.get("more_details", {})
        actionable = extract_actionable_fields(more_details)

        record["subscription_code"] = actionable["subscription_code"]
        record["subscription_number"] = actionable["subscription_number"]
        record["unsubscribe_code"] = actionable["unsubscribe_code"]
        record["unsubscribe_number"] = actionable["unsubscribe_number"]
        record["dial_code"] = actionable["dial_code"]

    with input_path.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2, ensure_ascii=False)

    print(f"Updated: {input_path}")