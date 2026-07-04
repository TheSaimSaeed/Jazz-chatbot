import json
import re
from pathlib import Path

# =====================================================
# Input JSON files
# =====================================================

INPUT_PATHS = [
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_cleaned.json"),
    Path(r"D:\Work\Scrapping\jazz-scrapping-bs4\jazz_offers_postpaid_cleaned.json"),
]


# =====================================================
# Validity Standardization
# =====================================================

def validity_to_standard(validity):
    """
    Standardize validity into a consistent format.

    Rules
    -----
    Days      -> Days
    Weeks     -> Days (1 Week = 7 Days)
    Months    -> Days (1 Month = 30 Days)
    Hours     -> Hours
    Minutes   -> Minutes

    Returns
    -------
    List[str]

    Examples
    --------
    Daily                    -> ['1 Day']
    Weekly                   -> ['7 Days']
    Monthly                  -> ['30 Days']
    7 Days                   -> ['7 Days']
    2 Weeks                  -> ['14 Days']
    3 Months                 -> ['90 Days']
    24 Hours                 -> ['24 Hours']
    60 Minutes               -> ['60 Minutes']
    1Day/7 Days/30 Days      -> ['1 Day', '7 Days', '30 Days']
    Daily / Weekly / Monthly -> ['1 Day', '7 Days', '30 Days']
    """

    if validity is None:
        return None

    text = str(validity).strip()

    if not text:
        return None

    # -------------------------------------------------
    # Normalize spacing
    # -------------------------------------------------

    text = re.sub(r"\s+", " ", text)

    # Handle missing spaces like:
    # 1Day -> 1 Day
    # 24Hours -> 24 Hours
    text = re.sub(
        r"(\d)(day|days|week|weeks|month|months|hour|hours|minute|minutes)",
        r"\1 \2",
        text,
        flags=re.IGNORECASE,
    )

    # -------------------------------------------------
    # Convert textual forms into numeric forms
    # -------------------------------------------------

    replacements = {
        r"\bdaily\b": "1 Day",
        r"\bweekly\b": "7 Days",
        r"\bmonthly\b": "30 Days",
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # -------------------------------------------------
    # Extract all validity values
    # -------------------------------------------------

    pattern = re.compile(
        r"(\d+)\s*(day|days|week|weeks|month|months|hour|hours|minute|minutes)",
        flags=re.IGNORECASE,
    )

    standardized = []

    for number, unit in pattern.findall(text):

        number = int(number)
        unit = unit.lower()

        if "day" in unit:

            value = f"{number} Day" if number == 1 else f"{number} Days"

        elif "week" in unit:

            days = number * 7
            value = f"{days} Day" if days == 1 else f"{days} Days"

        elif "month" in unit:

            days = number * 30
            value = f"{days} Day" if days == 1 else f"{days} Days"

        elif "hour" in unit:

            value = f"{number} Hour" if number == 1 else f"{number} Hours"

        elif "minute" in unit:

            value = f"{number} Minute" if number == 1 else f"{number} Minutes"

        else:
            continue

        standardized.append(value)

    # -------------------------------------------------
    # Remove duplicates while preserving order
    # -------------------------------------------------

    seen = set()
    result = []

    for item in standardized:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result or None


# =====================================================
# Process Files
# =====================================================

for input_path in INPUT_PATHS:

    print(f"\nProcessing: {input_path.name}")

    with input_path.open("r", encoding="utf-8") as f:
        records = json.load(f)

    updated = 0

    for record in records:

        standardized = validity_to_standard(record.get("validity"))

        # Save list version
        record["validity_standard"] = standardized

        # Normalize original validity field
        if standardized:
            record["validity"] = " / ".join(standardized)

        updated += 1

    with input_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"✓ Updated {updated} records.")

print("\n✅ Validity standardization completed successfully.")