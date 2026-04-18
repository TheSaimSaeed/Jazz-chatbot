import json
# Load JSON data from a file or string
with open('jazz_offers.json', 'r', encoding='utf-8') as file:
   data = json.load(file)
# Count items in the root array
count = len(data)
print(f"Number of JSON objects: {count}")