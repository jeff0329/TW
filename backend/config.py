import os
from dotenv import load_dotenv

load_dotenv(override=True)

# 配置文件 - 爬蟲和數據收集設置

# TDX API 配置。請以環境變數提供憑證，不要將金鑰寫入程式碼。
TDX_CONFIG = {
    "base_url": "https://tdx.transportdata.tw/api/tourism",
    "auth_url": "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token",
    "endpoints": {
        "scenic_spots": "/service/odata/V2/Tourism/Attraction",
        "restaurants": "/service/odata/V2/Tourism/Restaurant",
        "hotels": "/service/odata/V2/Tourism/Hotel",
        "activities": "/service/odata/V2/Tourism/Event"
    },
    "top_limit": 500,
    "app_id": os.getenv("TDX_APP_ID", ""),
    "app_key": os.getenv("TDX_APP_KEY", "")
}

# 具授權的旅遊資料 API（選配）。
AUTHORIZED_TRAVEL_API = {
    "url": os.getenv("TRAVEL_API_URL", ""),
    "key": os.getenv("TRAVEL_API_KEY", ""),
    "timeout": 30
}

# 旅遊網站配置
TRAVEL_WEBSITES = {
    "kkday": {
        "base_url": "https://www.kkday.com",
        "search_url": "https://www.kkday.com/zh-tw/search?keyword=",
        "selectors": {
            "product_cards": ".product-card, [data-id]",
            "title": ".product-title, .card-title",
            "price": ".price, [data-price]",
            "location": ".location, .destination"
        }
    },
    "klook": {
        "base_url": "https://www.klook.com",
        "search_url": "https://www.klook.com/zh-TW/search?query=",
        "selectors": {
            "product_cards": "[data-index]",
            "title": ".productTitle",
            "price": "[data-price]",
            "location": ".productLocation"
        }
    },
    "viator": {
        "base_url": "https://www.viator.com",
        "search_url": "https://www.viator.com/search?q=",
        "selectors": {
            "product_cards": ".product-card",
            "title": ".product-card-title",
            "price": ".product-card-price",
            "location": ".product-card-location"
        }
    }
}

# 台灣主要目的地
TAIWAN_DESTINATIONS = [
    "台北", "新北", "桃園", "新竹", "苗栗", 
    "台中", "彰化", "南投", "雲林", "嘉義",
    "台南", "高雄", "屏東", "花蓮", "台東", "宜蘭"
]

# 數據字段定義
DATA_SCHEMA = {
    "景點": ["景點名稱", "縣市", "分類", "描述", "地址", "開放時間", "票價", "經緯度", "圖片", "評分"],
    "餐廳": ["餐廳名稱", "縣市", "區域", "美食類別", "地址", "營業時間", "電話", "經緯度", "評分", "人均價格"],
    "飯店": ["飯店名稱", "縣市", "地址", "星級", "住宿價格", "經緯度", "評分", "設施"],
    "行程": ["行程標題", "天數", "預算", "目的地", "交通工具", "景點列表", "餐廳", "飯店", "難度", "評分"]
}

# 輸出格式
OUTPUT_FORMAT = "json"  # 支持 json, csv
OUTPUT_DIR = "./data"

# 日誌設置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "filename": "./logs/scraper.log"
}

# Ollama 配置
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "model": "qwen3:4b",
    "temperature": 0.7,
    "top_k": 40,
    "top_p": 0.9,
    "think": False,
    "num_predict": 256
}

# RAG 配置
RAG_CONFIG = {
    "chunk_size": 500,
    "chunk_overlap": 100,
    "vector_store": "./vector_db",
    "similarity_threshold": 0.7,
    "top_k": 5
}
