import base64
import csv
import json
import requests

# ==========================================
# CONFIGURATION: Set your credentials and parameters here!
# ==========================================
SCRAPERAPI_KEY = "98d5f813bacd8a64e9b461a19d2a267b"  # Put your free API key here
TARGET_ZIPCODE = "45202"                         # Put your target Ohio Zip Code here
SEARCH_RADIUS = "100"                             # Distance limit in miles (e.g. 25, 50, 100)
# ==========================================

def generate_dynamic_token(zipcode, miles):
    """Encodes parameters to match the website's request link structure exactly"""
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
    # The real target website page
    site_url = f"https://ohiomarijuanacommunity.com{token}"
    
    print(f"[SYSTEM LOG]: Routing request via clean residential network tunnel for Zip {TARGET_ZIPCODE}...")
    
    # Reroute request through ScraperAPI's proxy tunnel to bypass IP bans
    proxy_gateway_url = f"http://scraperapi.com?api_key={SCRAPERAPI_KEY}&url={site_url}"

    scraped_data = []

    try:
        # Request raw page through proxy channel
        response = requests.get(proxy_gateway_url, timeout=45)
        
        if response.status_code != 200:
            print(f"[ERROR]: Proxy connection rejected by server host. Code: {response.status_code}")
            write_safe_empty_file()
            return

        page_html = response.text
        
        # Intercept core structured data if available in Javascript components
        if "window.__NEXT_DATA__" in page_html:
            print("[SUCCESS]: Target database script parsed cleanly through firewall layer.")
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

        # Backup visual element scanner framework
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
            print("[NOTICE]: Clean connections made but zero dispensaries found inside radius criteria.")
            write_safe_empty_file()

    except Exception as e:
        print(f"[CRITICAL ERROR]: Proxy tunnel exception: {e}")
        write_safe_empty_file()

def save_to_csv(rows):
    output_file = "dispensary_menus.csv"
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Dispensary Name", "Product Name", "Category", "Price"])
        writer.writerows(rows)
    print(f"[SUCCESS]: Saved {len(rows)} live rows into your database repository file.")

def write_safe_empty_file():
    output_file = "dispensary_menus.csv"
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Dispensary Name", "Product Name", "Category", "Price"])
        writer.writerow(["No Local Menu Items Found", "Try increasing SEARCH_RADIUS or changing TARGET_ZIPCODE parameters", "N/A", "$0.00"])

if __name__ == "__main__":
    scrape_dispensary_menus()
