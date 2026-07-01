import json
import re
from pathlib import Path

input_path = Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_cleaned.json")
output_path = input_path
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
        line = re.sub(r"([(\[{])\s+", r"\1", line)
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

    # Light cleanup only; avoids changing codes or acronyms too aggressively.
    text = re.sub(r"\s{2,}", " ", text)
    return text

def normalize_record(record):
    cleaned = {}
    for key, value in record.items():
        if isinstance(value, str):
            if key == "plan_name":
                cleaned[key] = normalize_plan_name(value)
            else:
                cleaned[key] = normalize_whitespace(value)
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
    return cleaned

with input_path.open("r", encoding="utf-8") as file:
    records = json.load(file)

normalized_records = [normalize_record(record) for record in records]

with output_path.open("w", encoding="utf-8") as file:
    json.dump(normalized_records, file, indent=2, ensure_ascii=False)

print(f"Saved normalized data to: {output_path}")