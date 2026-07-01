import json
from pathlib import Path

input_path = Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_postpaid.json")
output_path = Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_postpaid_cleaned.json")

expected_keys = [
    "plan_name",
    "validity",
    "price",
    "data",
    "jazz_minutes",
    "sms",
    "other_network_minutes",
    "more_detail_url",
    "terms_and_conditions",
    "more_details",
]

def normalize(value):
    if value is None:
        return None
    if isinstance(value, str) and value.strip() in {"", "N/A"}:
        return None
    return value

with input_path.open("r", encoding="utf-8") as file:
    records = json.load(file)

cleaned_records = []
for record in records:
    cleaned = {key: None for key in expected_keys}
    for key, value in record.items():
        cleaned[key] = normalize(value)
    cleaned_records.append(cleaned)

with output_path.open("w", encoding="utf-8") as file:
    json.dump(cleaned_records, file, indent=2, ensure_ascii=False)