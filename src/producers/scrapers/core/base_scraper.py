import abc
import re

class BaseScraper(abc.ABC):
    
    @staticmethod
    def parse_quantity(product_name: str) -> int:
        """
        Dùng Regex để bóc tách số lượng sản phẩm từ text.
        VD: 'Combo 3 bỉm' -> 3, 'Mua 2 tặng 1' -> 2, 'Lốc 4 hộp' -> 4
        """
        name_lower = product_name.lower()
        
        # Pattern 1: x2, x3, x 4
        match = re.search(r'x\s*(\d+)', name_lower)
        if match: return int(match.group(1))
        
        # Pattern 2: combo 2, set 3, mua 2, lốc 4, thùng 6
        match = re.search(r'(combo|set|mua|lốc|thùng)\s*(\d+)', name_lower)
        if match: return int(match.group(2))
        
        # Pattern 3: 2 gói, 3 hộp, 4 bịch
        match = re.search(r'(\d+)\s*(gói|hộp|bịch|chai|lon|cuộn)', name_lower)
        if match: return int(match.group(1))
        
        return 1 # Mặc định là 1 unit nếu không tìm thấy

    @abc.abstractmethod
    def scrape_keyword(self, keyword: str, limit: int = 10) -> list:
        """
        Returns list of product dicts with schema:
        {
            'product_id': str/int,
            'product_name': str,
            'brand': str,
            'unit': str,
            'pack_quantity': int,
            'platform': str,
            'sale_price': int,
            'product_link': str
        }
        """
        pass
