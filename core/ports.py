from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

@dataclass
class Product:
    title: str
    price: float
    currency: str
    link: str
    source: str
    rating: float = 0.0         
    reviews: int = 0             
    condition: str = "New"       
    image_url: str = ""          
    description: str = ""
    product_id: str = ""

    def __repr__(self):
        return f"[{self.source}] {self.title[:30]}... (₹{self.price} | {self.reviews} reviews)"

class EcommerceProvider(ABC):
    @abstractmethod
    def search_products(self, 
                        query: str, 
                        max_price: float = None, 
                        min_price: float = 0, 
                        sort_by: str = "BEST_MATCH", 
                        condition: str = "ANY",
                        min_reviews: int = 0) -> List[Product]:
        pass