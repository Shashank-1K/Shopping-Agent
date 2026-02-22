import requests
import re
from typing import List
from core.ports import EcommerceProvider, Product

class UniversalSearchAdapter(EcommerceProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.host = "real-time-product-search.p.rapidapi.com"
        self.base_url = "https://real-time-product-search.p.rapidapi.com/search-v2"

    def search_products(self, query: str, max_price: float = None, min_price: float = 0, 
                        sort_by: str = "BEST_MATCH", condition: str = "ANY",
                        min_reviews: int = 0) -> List[Product]:
        
        print(f"[API] Searching: '{query}' on Amazon/Flipkart...")

        # 1. API Parameters
        querystring = {
            "q": query,
            "country": "in",
            "language": "en",
            "page": "1",
            "limit": "30",
            "sort_by": sort_by,
            "product_condition": condition,
            #  STORE SELECTION 
            "stores": "amazon,flipkart" 
        }
        
        if min_price: querystring["min_price"] = str(min_price)
        if max_price: querystring["max_price"] = str(max_price)

        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.host
        }

        try:

            response = requests.get(
                self.base_url,
                headers=headers,
                params=querystring,
                timeout=15
            )

            if response.status_code != 200:
                print(f"❌ API returned {response.status_code}")
                return []

            try:
                data = response.json()
            except ValueError:
                print("❌ Invalid JSON from API")
                return []


            
            products = []
            
            # 2. Parse Results
            items = []
            if 'data' in data and 'products' in data['data']:
                items = data['data']['products']
            elif 'data' in data and isinstance(data['data'], list):
                items = data['data']
            
            for item in items:
                try:
                    title = item.get('product_title', 'Unknown')
                    
                    # --- PARSE PRICE ---
                    offer = item.get('offer', {})
                    store = offer.get('store_name', 'Online')
                    
                    price_val = offer.get('price')
                    if not price_val: price_val = item.get('product_price')
                    if not price_val: continue

                    if isinstance(price_val, str):
                        clean = re.sub(r'[^\d.]', '', price_val)
                        price = float(clean) if clean else 0.0
                    else:
                        price = float(price_val)
                    
                    # --- PARSE REVIEWS & RATING ---
                    rating = float(item.get('product_rating', 0.0) or 0.0)
                    
                    # Robust Review Count Extraction
                    revs = item.get('product_num_reviews', 0)
                    if not revs: revs = item.get('reviews', 0)
                    reviews = int(revs) if revs else 0

                    # --- PARSE IMAGE ---
                    photos = item.get('product_photos', [])
                    img_url = photos[0] if isinstance(photos, list) and len(photos) > 0 else ""

                    # --- LINK ---
                    link = item.get('product_url')
                    if not link: link = item.get('offer', {}).get('offer_page_url')


                    # 3. FILTERING
                    if max_price and price > max_price: continue
                    if min_price and price < min_price: continue
                    
                    # Review Count Filter
                    if reviews < min_reviews: continue

                    products.append(Product(
                        title=title,
                        price=price,
                        currency="INR",
                        link=link,
                        source=store,
                        rating=rating,
                        reviews=reviews,
                        image_url=img_url
                    ))
                except Exception:
                    continue

            return products

        except Exception as e:
            print(f"❌ API Error: {e}")
            return []