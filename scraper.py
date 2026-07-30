import base64
import csv
import json
import requests
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURATION: Set your credentials and parameters here!
# ==========================================
SCRAPERAPI_KEY = "98d5f813bacd8a64e9b461a19d2a267b"  # Your functioning ScraperAPI Key
TARGET_ZIPCODE = "45202"                         # Target Zip Code
SEARCH_RADIUS = "100"                            # Search radius range in miles
# ==========================================

def generate_dynamic_token(zipcode, miles):
    """Generates the exact Base64 string required by the website configuration"""
    payload = {
        "cat": "flower",
        "med": "1",
        "market": "med",
        "sort": "name",
        "dir": "asc",
        "mode": "zip",
        "zip": str(zipcode),
        "dist": str(miles)
    }
    json_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    return base64.b64encode(json_bytes).decode('utf-8')

def scrape_dispensary_menus():
    token = generate_dynamic_token(TARGET_ZIPCODE, SEARCH_RADIUS)
    site_url = f"https://ohiomarijuanacommunity.com{token}"
    
    print(f"[SYSTEM LOG]: Tunnelling connection via ScraperAPI to target: {site_url}")
    proxy_gateway_url = f"http://scraperapi.com?api_key={SCRAPERAPI_KEY}&url={site_url}"

    scraped_data = []

    try:
        response = requests.get(proxy_gateway_url, timeout=45)
        
        if response.status_code != 200:
            print(f"[ERROR]: Connection refused by host server. Code: {response.status_code}")
            write_safe_empty_file("Proxy Error", f"HTTP Status {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Target the website's literal internal data storage script block
        script_tag = soup.find('script', id='__NEXT_DATA__')
        
        if script_tag:
            print("[SUCCESS]: Target database structure located in page headers.")
            json_data = json.loads(script_tag.string)
            
            # 2. Extract nested menu elements out of the app framework trees
            # This safely steps down through pageProps -> components -> listings variables
            props = json_data.get("props", {})
            page_props = props.get("pageProps", {})
            
            # Dynamic key extraction fallback scanner
            menu_items = page_props.get("menuItems", page_props.get("items", page_props.get("products", [])))
            
            if not menu_items and "initialState" in page_props:
                menu_items = page_props.get("initialState", {}).get("menus", {}).get("items", [])

            for item in menu_items:
                dispensary = item.get("dispensaryName", item.get("dispensary_name", "Nearby Dispensary"))
                product = item.get("productName", item.get("name", "Menu Item"))
                category = item.get("category", "Flower")
                raw_price = item.get("price", "N/A")
                
                if isinstance(raw_price, (int, float)):
                    price = f"${raw_price:.2f}"
                else:
                    price = f"${raw_price}" if "$" not in str(raw_price) else str(raw_price)

                scraped_data.append([dispensary, product, category, price])

        # 3. Fallback visual extraction if script parameters changed
        if not scraped_data:
            print("[NOTICE]: Script layer empty. Initializing visual extraction rules.")
            for card in soup.select('[class*="product-card"], [class*="menu-item"], .menu-item'):
                txt = card.get_text(" ", strip=True)
                if "$" in txt:
                    words = txt.split()
                    price = [w for w in words if "$" in w][0] if [w for w in words if "$" in w] else "N/A"
                    product = " ".join(words[:3])
                    scraped_data.append(["Nearby Dispensary", product, "Flower", price])

        # Save data straight to the spreadsheet repository
        if scraped_data:
            # Drop structural listing duplicates
            unique_rows = [list(x) for x in set(tuple(x) for x in scraped_data)]
            save_to_csv(unique_rows)
        else:
            print("[CRITICAL]: Core elements missing from source site payload.")
            write_safe_empty_file("Extraction Failure", "Website structural elements could not be parsed.")

    except Exception as e:
        print(f"[CRITICAL ERROR]: Pipeline execution stopped: {e}")
        write_safe_empty_file("Script Exception", str(e))

def save_to_csv(rows):
    output_file = "dispensary_menus.csv"
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Dispensary Name", "Product Name", "Category", "Price"])
        writer.writerows(rows)
    print(f"[SUCCESS]: Saved {len(rows)} live rows directly to your database.")

def write_safe_empty_file(status, message):
    output_file = "dispensary_menus.csv"
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Dispensary Name", "Product Name", "Category", "Price"])
        writer.writerow([status, message, "N/A", "$0.00"])

if __name__ == "__main__":
    scrape_dispensary_menus()
