import base64
import csv
import json
import requests

# ==========================================
# CONFIGURATION: Change these to your exact neighborhood data!
# ==========================================
TARGET_ZIPCODE = "45238"  # Put your target Ohio Zip Code here
SEARCH_RADIUS = "40"      # Put your distance limit in miles here (e.g. 10, 25, 50)
# ==========================================

def generate_dynamic_token(zipcode, miles):
    """Encodes parameters to exactly match the website's dynamic request link structure"""
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
    target_url = f"https://ohiomarijuanacommunity.com{token}"
    
    print(f"[LOG]: Scanning Ohio Zip {TARGET_ZIPCODE} ({SEARCH_RADIUS} mile radius)...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.ohiomarijuanacommunity.com/dispensaries",
        "Connection": "keep-alive"
    }

    scraped_data = []

    try:
        session = requests.Session()
        response = session.get(target_url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"[ERROR]: Request blocked. HTTP status code: {response.status_code}")
            write_safe_empty_file()
            return

        page_html = response.text
        
        # Check if the website's framework object can be read directly
        if "window.__NEXT_DATA__" in page_html:
            start_idx = page_html.find("window.__NEXT_DATA__ = ") + len("window.__NEXT_DATA__ = ")
            end_idx = page_html.find(";</script>", start_idx)
            json_raw = page_html[start_idx:end_idx]
            
            clean_json = json.loads(json_raw)
            items = clean_json.get("props", {}).get("pageProps", {}).get("initialState", {}).get("menuItems", [])
            
            for item in items:
                dispensary = item.get("dispensaryName", "Nearby Dispensary")
                product = item.get("productName", "Menu Item")
                category = item.get("category", "Flower")
                price = f"${item.get('price', 0.00):.2f}" if isinstance(item.get('price'), (int, float)) else item.get('price', 'N/A')
                scraped_data.append([dispensary, product, category, price])

        # Backup DOM extraction framework
        if not scraped_data:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_html, 'html.parser')
            elements = soup.find_all(lambda tag: tag.name in ['div', 'li'] and tag.has_attr('class'))
            for elem in elements:
                txt = elem.get_text(" ", strip=True)
                if "$" in txt and len(txt) < 200:
                    lines = [line.strip() for line in txt.split(" ") if line.strip()]
                    if len(lines) >= 3:
                        price_tags = [l for l in lines if "$" in l]
                        price = price_tags[0] if price_tags else "N/A"
                        product_name = " ".join(lines[:3])
                        
                        if any(x in product_name.lower() for x in ["filter", "menu", "search", "login", "cookie"]):
                            continue
                            
                        scraped_data.append(["Dispensary", product_name, "Flower", price])

        # Remove duplicate data records
        unique_rows = [list(x) for x in set(tuple(x) for x in scraped_data)]

        if unique_rows:
            save_to_csv(unique_rows)
        else:
            print("[NOTICE]: Zero local rows found. Writing safe blank structure.")
            write_safe_empty_file()

    except Exception as e:
        print(f"[CRITICAL ERROR]: Pipeline exception caught: {e}")
        write_safe_empty_file()

def save_to_csv(rows):
    output_file = "dispensary_menus.csv"
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Dispensary Name", "Product Name", "Category", "Price"])
        writer.writerows(rows)
    print(f"[SUCCESS]: Saved {len(rows)} entries into the spreadsheet source.")

def write_safe_empty_file():
    """Outputs structured column headers with an empty data row to prevent Google Sheets parsing bugs."""
    output_file = "dispensary_menus.csv"
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Dispensary Name", "Product Name", "Category", "Price"])
        writer.writerow(["No Local Menu Items Found", "Try increasing SEARCH_RADIUS or changing TARGET_ZIPCODE parameters", "N/A", "$0.00"])
    print("[SYSTEM LOG]: Safe file output complete.")

if __name__ == "__main__":
    scrape_dispensary_menus()
