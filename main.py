import requests
from bs4 import BeautifulSoup
import csv
import json


URL = 'https://jazz.com.pk/prepaid/'
headers = {
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

response = requests.get(URL, headers=headers)
#print(response.text)

soup=BeautifulSoup(response.text, 'html.parser')
cards=soup.find_all('div', class_='offer-box')

plans = []

for i, card in enumerate(cards):
    try:
        # Extract plan name
        h5 = card.find('h5', class_='color-grey')
        h4 = card.find('h4', class_='color-red')
        plan_name = f"{h5.get_text().strip()} {h4.get_text().strip()}".strip()
        
        # Extract price
        price_div = card.find('div', class_='offer-price')
        price = f"{price_div.get_text().strip()}".strip() if price_div else "N/A"
        
        # Extract URL
        url = card.find('a')
        more_detail_url = url.get('href') if url else "N/A"

        # Extract details from the details section
        details_h5 = card.find('h5', attrs={'data-offer': True})
        details_text = details_h5.get_text() if details_h5 else ""
        
        # Parse each detail line
        details_dict = {}
        for p in details_h5.find_all('p') if details_h5 else []:
            detail_line = p.get_text().strip()
            if detail_line:
                details_dict[detail_line] = detail_line

        # Extract specific fields from details
        data = "N/A"
        jazz_minutes = "N/A"
        sms = "N/A"
        other_network_minutes = "N/A"
        validity = "N/A"
        
        for line in details_dict.keys():
            if 'GB' in line or 'Data' in line:
                data = line
            elif 'On-Net' in line or 'Jazz' in line or 'Unlimited' in line:
                jazz_minutes = line
            elif 'SMS' in line:
                sms = line
            elif 'Other Network' in line or 'Network Mins' in line:
                other_network_minutes = line


        
        if 'Weekly' in plan_name:
            validity = "7 Days"
        elif 'Monthly' in plan_name:
            validity = "30 Days"
        elif 'Daily' in plan_name:
            validity = "1 Day"
        elif '3 Days' in plan_name:
            validity = "3 Days"

        plan = {
            "plan_name": plan_name,
            "validity": validity,
            "price": price,
            "data": data,
            "jazz_minutes": jazz_minutes,
            "sms": sms,
            "other_network_minutes": other_network_minutes,
            "more_detail_url": more_detail_url
        }

        #---More details extraction---
        if more_detail_url != "N/A":
            more_detail_response = requests.get(more_detail_url, headers=headers)
            more_detail_soup = BeautifulSoup(more_detail_response.text, 'html.parser')
            inner_content = more_detail_soup.find('div', class_='inner-content-detail')
            if inner_content:
                li_items = inner_content.find_all('li')
                details_dict = {}
                for li in li_items:
                    spans = li.find_all('span')
                    if len(spans) >= 2:
                        title = spans[0].get_text().strip()
                        value = spans[1].get_text().strip()
                        details_dict[title] = value
            plan['more_details'] = details_dict
            print(f"Extracting more details for card {i+1}")

            
            terms_section = more_detail_soup.find('div', class_='collapse show')
            if terms_section:
                terms_text = terms_section.get_text().strip()
                plan['terms_and_conditions'] = terms_text
                print(f"Extracting terms and conditions for card {i+1}...") 
            else:
                plan['terms_and_conditions'] = "N/A"

        plans.append(plan)
        print(f"Extracted plan name: {plan_name}")

    except Exception as e:
        print(f"Error processing card {i+1}: {str(e)}")
        continue


# Save to JSON file
with open('jazz_offers.json', 'w', encoding='utf-8') as f:
    json.dump(plans, f, indent=2, ensure_ascii=False)

# Display results
print(f"\n\nTotal plans extracted: {len(plans)}\n")


print("\nExtracted Plans:")

for plan in plans:
    print(plan['plan_name'])




'''
card10 = cards[9]

content_cards=card10.find('div', class_='offer-box-content-wrap')
offer_price=card10.find('div', class_='offer-price').get_text()
more_detail_link=card10.find('a').get('href')

print(content_cards)
print(offer_price)  
print(more_detail_link)

'''





'''
for i, card in enumerate(cards):
    print("checking card number:", i+1)
   
    content_cards=card.find('div', class_='offer-box-content-wrap').get_text()
    offer_price=card.find('div', class_='offer-price').get_text()
    more_detail_link=card.find('a').get('href')

    moreDetailreq=requests.get(more_detail_link, headers=headers)
    moreDetailSoup=BeautifulSoup(moreDetailreq.text, 'html.parser')

    contentDetail=moreDetailSoup.find('div', class_='inner-content-detail').get_text()
    print([str(content_cards), str(offer_price), str(contentDetail)])
    
    with open('jazz_offers.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([str(content_cards), str(offer_price), str(contentDetail)])

'''