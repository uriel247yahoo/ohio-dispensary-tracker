import base64
import json
import csv
import requests
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURATION: Change these two values whenever you want!
# ==========================================
TARGET_ZIPCODE = "43215"  # Put your Ohio Zip Code here
SEARCH_RADIUS = "25"      # Put your distance limit in miles here (e.g. 10, 25, 50)
# ==========================================

def generate_encoded_url(zipcode, miles):
    menu_settings = {
        "cat": "flower",
        "med": "1",
        "market": "med",
        "sort": "name",
        "dir": "asc",
        "mode": "zip",
        "zip": str(zipcode),
        "dist": str(miles)
    }
    json_str = json.dumps(menu_settings, separators=(',', ':'))
    encoded_string = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    return f"https://ohiomarijuanacommunity.com{encoded_string}"

def scrape_dispensary_menus():
    target_url = generate_encoded_url(TARGET_ZIPCODE, SEARCH_RADIUS)
    print(f"Targeting URL: {target_url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }
    
    response = requests.get(target_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to connect. Site returned code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    scraped_data = []

    # NEW ADVANCED SCANNER: Looks at every text block on the page dynamically
    for element in soup.find_all(['div', 'tr', 'li', 'article']):
        text_content = element.get_text(separator=" ", strip=True)
        
        # Look for standard price symbols to identify product blocks
        if "$" in text_content and len(text_content) < 300:
            words = text_content.split()
            if len(words) > 2:
                # Break down text blocks into rough fields safely
                price = [w for w in words if "$" in w][0]
                name = " ".join(words[:3]) # First few words usually contain the brand/strain
                dispensary = "Nearby Dispensary"
                
                # Filter out obvious structural webpage junk lines
                if "menu" in name.lower() or "filter" in name.lower():
                    continue
                    
                scraped_data.append([dispensary, name, "Flower", price])

    # If the fallback scanner fails, log a safe mock line so your pipeline never crashes
    if not scraped_data:
        print("Notice: No live items found matching layout constraints. Writing database template.")
        scraped_data.append(["No Dispensaries Found", "Adjust zip code or radius parameters", "N/A", "$0.00"])

    # Eliminate duplicate scraped rows
    unique_data = [list(x) for x in set(tuple(x) for x in scraped_data)]

    output_file = "dispensary_menus.csv"
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Dispensary Name", "Product Name", "Category", "Price"])
        writer.writerows(unique_data)
        
    print(f"Success! Processed {len(unique_data)} entries into your app database.")

if __name__ == "__main__":
    scrape_dispensary_menus()
