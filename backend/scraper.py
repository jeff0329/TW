"""
台灣旅遊數據爬蟲模組
負責從 TDX API 和多個旅遊網站收集數據
"""

import requests
import json
import csv
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import time

try:
    from .config import TDX_CONFIG, TRAVEL_WEBSITES, TAIWAN_DESTINATIONS, OUTPUT_DIR, LOGGING_CONFIG
except ImportError:  # pragma: no cover - fallback for direct script execution
    from backend.config import TDX_CONFIG, TRAVEL_WEBSITES, TAIWAN_DESTINATIONS, OUTPUT_DIR, LOGGING_CONFIG

Path(LOGGING_CONFIG["filename"]).parent.mkdir(parents=True, exist_ok=True)

# 設定日誌
logging.basicConfig(**LOGGING_CONFIG)
logger = logging.getLogger(__name__)

class TDXScraper:
    """台灣交通部 TDX API 爬蟲"""
    
    def __init__(self):
        self.base_url = TDX_CONFIG["base_url"]
        self.access_token: Optional[str] = None
        self.token_expires_at = 0.0
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Taiwan-Travel-Planning-App/1.0",
            "Accept-Encoding": "gzip, br",
        }

    def _get_access_token(self) -> str:
        if self.access_token and time.monotonic() < self.token_expires_at:
            return self.access_token
        app_id = TDX_CONFIG.get("app_id")
        app_key = TDX_CONFIG.get("app_key")
        if not app_id or not app_key:
            raise RuntimeError("缺少 TDX_APP_ID 或 TDX_APP_KEY，請先申請 TDX API 憑證")
        response = self.session.post(
            TDX_CONFIG["auth_url"],
            data={"grant_type": "client_credentials", "client_id": app_id, "client_secret": app_key},
            timeout=30,
        )
        if response.status_code == 401:
            raise RuntimeError("TDX OAuth 驗證失敗，請確認 Client ID 與 Client Secret 已完整複製且仍有效")
        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data["access_token"]
        expires_in = max(60, int(token_data.get("expires_in", 86400)))
        self.token_expires_at = time.monotonic() + expires_in - 60
        return self.access_token

    def _get(self, url: str) -> requests.Response:
        headers = dict(self.headers)
        headers["Authorization"] = f"Bearer {self._get_access_token()}"
        response = self.session.get(url, headers=headers, timeout=30)
        if response.status_code == 401:
            self.access_token = None
            self.token_expires_at = 0.0
            headers["Authorization"] = f"Bearer {self._get_access_token()}"
            response = self.session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response

    @staticmethod
    def _address(item: Dict[str, Any]) -> Dict[str, str]:
        address = item.get("PostalAddress") or {}
        return {
            "縣市": address.get("City", ""),
            "區域": address.get("Town", ""),
            "地址": address.get("StreetAddress", ""),
        }

    @staticmethod
    def _position(item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "經度": item.get("PositionLon", ""),
            "緯度": item.get("PositionLat", ""),
        }

    @staticmethod
    def _phone(item: Dict[str, Any]) -> str:
        telephones = item.get("Telephones") or []
        return str(telephones[0].get("Tel", "")) if telephones else ""

    @staticmethod
    def _image(item: Dict[str, Any]) -> str:
        images = item.get("Images") or []
        return str(images[0].get("URL", "")) if images else ""
        
    def fetch_scenic_spots(self) -> List[Dict[str, Any]]:
        """Fetch scenic spots across Taiwan"""
        logger.info("Starting to fetch scenic spot data...")
        endpoint = self.base_url + TDX_CONFIG["endpoints"]["scenic_spots"]
        
        processed_data = []
        try:
            url = f"{endpoint}?$top={TDX_CONFIG['top_limit']}&$format=JSON"
            response = self._get(url)
            
            if response.status_code == 200:
                raw_data = response.json()
                
                for spot in raw_data:
                    address = self._address(spot)
                    position = self._position(spot)
                    item = {
                        "type": "景點",
                        "名稱": spot.get("AttractionName", ""),
                        **address,
                        "分類": ", ".join(map(str, spot.get("AttractionClasses") or [])),
                        "描述": spot.get("Description") or "尚無詳細描述",
                        "開放時間": spot.get("ServiceTimeInfo", ""),
                        "票價": spot.get("FeeInfo", ""),
                        **position,
                        "圖片": self._image(spot),
                        "電話": self._phone(spot),
                        "網站": spot.get("WebsiteUrl", ""),
                        "來源": "TDX"
                    }
                    processed_data.append(item)
                
                logger.info(f"Successfully fetched {len(processed_data)} scenic spots")
            else:
                logger.error(f"API error: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching scenic spots: {e}")
            raise RuntimeError(f"TDX 景點資料取得失敗: {e}") from e

        return processed_data
    
    def fetch_restaurants(self) -> List[Dict[str, Any]]:
        """Fetch restaurants across Taiwan"""
        logger.info("Starting to fetch restaurant data...")
        endpoint = self.base_url + TDX_CONFIG["endpoints"]["restaurants"]
        
        processed_data = []
        try:
            url = f"{endpoint}?$top={TDX_CONFIG['top_limit']}&$format=JSON"
            response = self._get(url)
            
            if response.status_code == 200:
                raw_data = response.json()
                
                for restaurant in raw_data:
                    address = self._address(restaurant)
                    position = self._position(restaurant)
                    item = {
                        "type": "餐廳",
                        "名稱": restaurant.get("RestaurantName", ""),
                        **address,
                        "分類": ", ".join(map(str, restaurant.get("CuisineClasses") or [])),
                        "描述": restaurant.get("Description", ""),
                        "營業時間": restaurant.get("ServiceTimeInfo", ""),
                        **position,
                        "圖片": self._image(restaurant),
                        "電話": self._phone(restaurant),
                        "網站": restaurant.get("WebsiteUrl", ""),
                        "來源": "TDX"
                    }
                    processed_data.append(item)
                
                logger.info(f"Successfully fetched {len(processed_data)} restaurants")
            else:
                logger.error(f"API error: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching restaurants: {e}")
            raise RuntimeError(f"TDX 餐廳資料取得失敗: {e}") from e

        return processed_data
    
    def fetch_hotels(self) -> List[Dict[str, Any]]:
        """Fetch hotels across Taiwan"""
        logger.info("Starting to fetch hotel data...")
        endpoint = self.base_url + TDX_CONFIG["endpoints"]["hotels"]
        
        processed_data = []
        try:
            url = f"{endpoint}?$top={TDX_CONFIG['top_limit']}&$format=JSON"
            response = self._get(url)
            
            if response.status_code == 200:
                raw_data = response.json()
                
                for hotel in raw_data:
                    address = self._address(hotel)
                    position = self._position(hotel)
                    item = {
                        "type": "飯店",
                        "名稱": hotel.get("HotelName", ""),
                        **address,
                        "分類": ", ".join(map(str, hotel.get("HotelClasses") or [])),
                        "描述": hotel.get("Description", ""),
                        "地址": address["地址"],
                        "房型": hotel.get("RoomInfo", ""),
                        "星級": hotel.get("HotelStars", ""),
                        "最低房價": hotel.get("LowestPrice", ""),
                        **position,
                        "圖片": self._image(hotel),
                        "電話": self._phone(hotel),
                        "網站": hotel.get("WebsiteUrl", ""),
                        "來源": "TDX"
                    }
                    processed_data.append(item)
                
                logger.info(f"Successfully fetched {len(processed_data)} hotels")
            else:
                logger.error(f"API error: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching hotels: {e}")
            raise RuntimeError(f"TDX 飯店資料取得失敗: {e}") from e

        return processed_data


class DataProcessor:
    """數據處理和統一格式"""
    
    @staticmethod
    def save_json(data: List[Dict], filename: str) -> None:
        """Save data in JSON format"""
        output_path = Path(OUTPUT_DIR) / filename
        Path(OUTPUT_DIR).mkdir(exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"JSON file saved: {output_path}")
    
    @staticmethod
    def save_csv(data: List[Dict], filename: str) -> None:
        """Save data in CSV format"""
        if not data:
            logger.warning("No data to save")
            return
        
        output_path = Path(OUTPUT_DIR) / filename
        Path(OUTPUT_DIR).mkdir(exist_ok=True)
        
        # Collect all unique keys from all data items
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
        keys = list(all_keys)
        
        with open(output_path, "w", encoding="utf-8-sig", newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys, restval='')
            dict_writer.writeheader()
            dict_writer.writerows(data)
        
        logger.info(f"CSV file saved: {output_path}")
    
    @staticmethod
    def merge_data(datasets: Dict[str, List[Dict]]) -> List[Dict]:
        """Merge multiple datasets"""
        merged = []
        for data in datasets.values():
            merged.extend(data)
        
        logger.info(f"Merged {len(merged)} data items")
        return merged
    
    @staticmethod
    def deduplicate(data: List[Dict], key: str = "名稱") -> List[Dict]:
        """Remove duplicates from data"""
        seen = set()
        unique_data = []
        
        for item in data:
            identifier = f"{item.get(key, '')}-{item.get('縣市', '')}"
            if identifier not in seen:
                unique_data.append(item)
                seen.add(identifier)
        
        logger.info(f"Deduplication complete: {len(unique_data)} items (removed {len(data) - len(unique_data)} duplicates)")
        return unique_data


def main():
    """Main program - Execute all scraper tasks"""
    logger.info("=" * 50)
    logger.info("Starting Taiwan tourism data scraper")
    logger.info("=" * 50)
    
    scraper = TDXScraper()
    processor = DataProcessor()
    
    # 抓取所有數據
    all_data = {
        "景點": scraper.fetch_scenic_spots(),
        "餐廳": scraper.fetch_restaurants(),
        "飯店": scraper.fetch_hotels()
    }
    
    # 合併所有數據
    merged_data = processor.merge_data(all_data)
    
    # 去重
    unique_data = processor.deduplicate(merged_data)
    
    # 保存數據
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    processor.save_json(unique_data, f"taiwan_tourism_data_{timestamp}.json")
    processor.save_csv(unique_data, f"taiwan_tourism_data_{timestamp}.csv")
    
    # 分類保存
    for category, data in all_data.items():
        if data:
            processor.save_json(data, f"{category}_{timestamp}.json")
            processor.save_csv(data, f"{category}_{timestamp}.csv")
    
    logger.info("=" * 50)
    logger.info(f"Scraper execution complete. Total data collected: {len(unique_data)} items")
    logger.info("=" * 50)
    
    return unique_data


if __name__ == "__main__":
    data = main()
