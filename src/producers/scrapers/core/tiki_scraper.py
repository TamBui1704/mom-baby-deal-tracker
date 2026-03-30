import requests
import time
import random
from .base_scraper import BaseScraper

class TikiScraper(BaseScraper):
    def scrape_keyword(self, keyword: str, limit: int = 10) -> list:
        print(f"[Tiki] Searching for '{keyword}'...")
        url = "https://tiki.vn/api/v2/products"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        }
        params = {"q": keyword, "limit": limit}
        
        try:
            time.sleep(random.uniform(1, 3)) # Polite delay
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                products = []
                for item in data.get('data', []):
                    products.append({
                        'product_id': str(item.get('id', '')),
                        'product_name': item.get('name', ''),
                        'brand': item.get('brand_name', 'No Brand'),
                        'unit': 'Cái', # Default unit
                        'pack_quantity': self.parse_quantity(item.get('name', '')),
                        'sale_price': int(item.get('price', 0)),
                        'product_link': f"https://tiki.vn/{item.get('url_path', '')}"
                    })
                print(f"[Tiki] Found {len(products)} products for '{keyword}'.")
                return products
            else:
                print(f"[Tiki] Error fetching {keyword}: HTTP {resp.status_code}")
                return []
        except Exception as e:
            print(f"[Tiki] Request Exception: {e}")
            return []
