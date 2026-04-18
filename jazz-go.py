import requests
from bs4 import BeautifulSoup
import json
import re

BASE_URL = "https://jazz.com.pk"
URL = f"{BASE_URL}/prepaid/"

HEADERS = {
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}


def fetch_html():
    session = requests.Session()
    res = session.get(URL, headers=HEADERS)
    res.raise_for_status()
    return res.text


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def extract_number(text):
    match = re.search(r"[\d.]+", text)
    return match.group(0) if match else None


def parse_bundles(html):
    soup = BeautifulSoup(html, "html.parser")

    bundles = []

    # 🔥 Jazz bundles are usually inside cards
    cards = soup.select("div.card, div.bundle, div.product, div.plan")

    for card in cards:
        try:
            # ---- PLAN NAME ----
            name_tag = card.select_one("h2, h3, h4, .title")
            plan_name = clean_text(name_tag.get_text()) if name_tag else None

            # ---- PRICE ----
            price_tag = card.find(string=re.compile(r"Rs|PKR", re.I))
            price = clean_text(price_tag) if price_tag else None

            # ---- VALIDITY ----
            validity_tag = card.find(string=re.compile(r"day|hour|week|month", re.I))
            validity = clean_text(validity_tag) if validity_tag else None

            # ---- FEATURES ----
            features = card.select("li, .feature, .benefit")

            data = jazz_minutes = sms = other_minutes = None

            for f in features:
                text = clean_text(f.get_text())

                if re.search(r"gb|mb", text, re.I):
                    data = text
                elif re.search(r"jazz|on[- ]net", text, re.I):
                    jazz_minutes = text
                elif re.search(r"sms", text, re.I):
                    sms = text
                elif re.search(r"other|off[- ]net", text, re.I):
                    other_minutes = text

            # ---- DETAILS URL ----
            link_tag = card.find("a", href=True)
            more_url = BASE_URL + link_tag["href"] if link_tag else None

            # Skip junk cards
            if not plan_name:
                continue

            bundles.append({
                "plan_name": plan_name,
                "validity": validity,
                "price": price,
                "data": data,
                "jazz_minutes": jazz_minutes,
                "sms": sms,
                "other_network_minutes": other_minutes,
                "more_detail_url": more_url
            })

        except Exception as e:
            print("Skipped one card:", e)

    return bundles


def save_json(data, filename="jazz_prepaid.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    html = fetch_html()
    bundles = parse_bundles(html)
    save_json(bundles)

    print(f"✅ Scraped {len(bundles)} bundles")