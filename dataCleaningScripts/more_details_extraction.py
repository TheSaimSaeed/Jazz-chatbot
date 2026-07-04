import json
from pathlib import Path

input_paths = [
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_cleaned.json"),
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_postpaid_cleaned.json"),
]

for input_path in input_paths:
    output_path = input_path.with_name(f"{input_path.stem}_more_details.json")

    with input_path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    extracted = []
    for record in records:
        extracted.append({
            "plan_name": record.get("plan_name"),
            "more_details": record.get("more_details", {})
        })

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(extracted, file, indent=2, ensure_ascii=False)

    print(f"Saved: {output_path}")