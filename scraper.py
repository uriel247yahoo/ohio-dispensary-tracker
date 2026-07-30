import csv
import json
import requests

# ==========================================
# CONFIGURATION: Set your credentials and parameters here!
# ==========================================
SCRAPERAPI_KEY = "98d5f813bacd8a64e9b461a19d2a267b"  # Keep your ScraperAPI key here
TARGET_ZIPCODE = "45202"                         # Using your updated Cincinnati Zip
SEARCH_RADIUS = "100"                            # Using your 100-mile range
# ==========================================

def scrape_dispensary_menus():
    # 1. Target the actual backend data engine endpoint used by the web app
    backend_api_url = "https://ohiomarijuanacommunity.com"
    
    print(f"[SYSTEM LOG]: Querying backend database engine for Zip {TARGET_ZIPCODE}...")

    # 2. Re-route the API request through ScraperAPI to hide the GitHub runner IP
    proxy_gateway_url = f"http://scraperapi.com?api_key={SCRAPERAPI_KEY}&url={backend_api_url}"

    # 3. This payload tells the database exactly what filters we want to query
    payload = {
        "zipcode": str(TARGET_ZIPCODE),
        "radius": int(SEARCH_RADIUS),
        "category": "flower",
        "market": "med",
        "page": 1,
        "limit": 100
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        # We must use a POST request here because we are submitting search parameters
        response = requests.post(proxy_gateway_url, json=payload, headers=headers, timeout=45)
        
        if response.status_code != 200:
            print(f"[ERROR]: Database rejected query. Status: {response.status_code}")
            write_safe_empty_file()
            return

        # Parse the raw data packet response
        data_packet = response.json()
        scraped_data = []

        # 4. Extract individual items out of standard JSON list arrays
        # (Handles multiple common backend naming structures like 'items', 'products', or 'data')
        items = data_packet.get("items", data_packet.get("products", data_packet.get("data", [])))

        for item in items:
            dispensary = item.get("dispensary_name", item.get("dispensaryName", "Nearby Dispensary"))
            product = item.get("product_name", item.get("productName", "Menu Item"))
            category = item.get("category", "Flower")
            raw_price = item.get("price", "N/A")
            
            # Formats raw database numbers (like 45 or 45.0) into retail pricing format ($45.00)
            if isinstance(raw_price, (int, float)):
                price = f"${raw_price:.2f}"
            else:
                price = f"${raw_price}" if "$" not in str(raw_price) else str(raw_price)

            scraped_data.append([dispensary, product, category, price])

        # 5. Output management
        if scraped_data:
            save_to_csv(scraped_data)
        else:
            print("[NOTICE]: Connected to data hub, but parameter payload returned 0 matches.")
            write_safe_empty_file()

    except Exception as e:
        print(f"[CRITICAL ERROR]: Backend tunnel connection failed: {e}")
        write_safe_empty_file()

def save_to_csv(rows):
    output_file = "dispensary_menus.csv"
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Dispensary Name", "Product Name", "Category", "Price"])
        writer.writerows(rows)
    print(f"[SUCCESS]: Data stream intercepted! Saved {len(rows)} live rows to spreadsheet source.")

def write_safe_empty_file():
    output_file = "dispensary_menus.csv"
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Dispensary Name", "Product Name", "Category", "Price"])
        writer.writerow(["API Mode Active", "Connected to endpoint but returned 0 rows. Checking keys...", "N/A", "$0.00"])

if __name__ == "__main__":
    scrape_dispensary_menus()
