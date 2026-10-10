"""旅遊資料蒐集、清理與知識庫建立工具。

TDX 是主要的官方資料來源；DynamicTravelScraper 可用於經授權的動態網站。
"""

import csv
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote_plus

try:
    from backend.config import AUTHORIZED_TRAVEL_API, OUTPUT_DIR, TRAVEL_WEBSITES
except ImportError:  # pragma: no cover - fallback for direct script execution
    from .backend.config import AUTHORIZED_TRAVEL_API, OUTPUT_DIR, TRAVEL_WEBSITES

logger = logging.getLogger(__name__)


class TourismDataPipeline:
    """將多來源旅遊資料清理成可供 RAG 使用的標準格式。"""

    TEXT_FIELDS = ("名稱", "縣市", "區域", "分類", "描述", "地址", "網站", "來源")

    def normalize_item(self, item: Dict[str, Any], source: str = "unknown") -> Dict[str, Any]:
        normalized = dict(item)
        normalized["type"] = self._first_value(
            item, "type", "類型", default="景點" if item.get("景點名稱") else "未分類"
        )
        normalized["名稱"] = self._first_value(item, "名稱", "景點名稱", "餐廳名稱", "飯店名稱", "標題")
        address = str(self._first_value(item, "地址", "Address", default=""))
        city = self._first_value(item, "縣市", "城市", "目的地")
        normalized["縣市"] = city or self._extract_city(address)
        normalized["區域"] = self._first_value(item, "區域", "鄉鎮", "行政區") or self._extract_area(address)
        normalized["描述"] = self._first_value(item, "描述", "詳細描述", "內容", "介紹", default="")
        if item.get("經緯度") and not item.get("經度") and not item.get("緯度"):
            parts = [part.strip() for part in str(item["經緯度"]).split(",")]
            if len(parts) == 2:
                normalized["緯度"], normalized["經度"] = parts
        normalized["來源"] = self._first_value(item, "來源", "source", default=source)
        normalized["抓取時間"] = self._first_value(
            item, "抓取時間", default=datetime.now(timezone.utc).isoformat()
        )
        for key in self.TEXT_FIELDS:
            normalized[key] = self._clean_text(normalized.get(key, ""))
        return normalized

    @staticmethod
    def _first_value(item: Dict[str, Any], *keys: str, default: str = "") -> Any:
        for key in keys:
            value = item.get(key)
            if value is not None and str(value).strip():
                return value
        return default

    @staticmethod
    def _clean_text(value: Any) -> str:
        text = "" if value is None else str(value)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _extract_city(address: str) -> str:
        match = re.match(r"^([^縣市]+[縣市])", address)
        return match.group(1) if match else ""

    @staticmethod
    def _extract_area(address: str) -> str:
        match = re.match(r"^[^縣市]+[縣市]([^鄉鎮市區]+[鄉鎮市區])", address)
        return match.group(1) if match else ""

    def clean(self, items: Iterable[Dict[str, Any]], source: str = "unknown") -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        seen = set()
        for raw_item in items:
            item = self.normalize_item(raw_item, source)
            name = item["名稱"]
            if not name:
                continue
            identity = (item["type"], name.casefold(), item["縣市"].casefold())
            if identity in seen:
                continue
            seen.add(identity)
            result.append(item)
        return result

    def quality_report(self, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        records = list(items)
        is_schema_native = bool(records) and "source_type" in records[0]
        if is_schema_native:
            required = ("name", "source_type", "city", "description", "source")
            missing = {field: sum(not str(item.get(field, "")).strip() for item in records) for field in required}
            return {
                "total": len(records),
                "valid_names": sum(bool(str(item.get("name", "")).strip()) for item in records),
                "missing_required_fields": missing,
                "types": self._counts(records, "source_type"),
                "sources": self._counts(records, "source"),
            }
        required = ("名稱", "type", "縣市", "描述", "來源")
        missing = {field: sum(not str(item.get(field, "")).strip() for item in records) for field in required}
        return {
            "total": len(records),
            "valid_names": sum(bool(str(item.get("名稱", "")).strip()) for item in records),
            "missing_required_fields": missing,
            "types": self._counts(records, "type"),
            "sources": self._counts(records, "來源"),
        }

    @staticmethod
    def _counts(items: Iterable[Dict[str, Any]], field: str) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for item in items:
            value = str(item.get(field) or "未分類")
            counts[value] = counts.get(value, 0) + 1
        return counts

    def save(self, items: List[Dict[str, Any]], filename: Optional[str] = None) -> Path:
        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / (filename or f"taiwan_tourism_data_{datetime.now():%Y%m%d_%H%M%S}.json")
        target.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        return target


class AuthorizedTravelAPI:
    """擷取已取得授權的旅遊 API，並轉成統一資料格式。"""

    def __init__(self, url: str = "", api_key: str = "", timeout: int = 30):
        self.url = url or AUTHORIZED_TRAVEL_API["url"]
        self.api_key = api_key or AUTHORIZED_TRAVEL_API["key"]
        self.timeout = max(1, int(timeout or AUTHORIZED_TRAVEL_API["timeout"]))

    def search(self, keyword: str, limit: int = 30) -> List[Dict[str, Any]]:
        import requests

        keyword = str(keyword or "").strip()
        if not self.url:
            raise RuntimeError("未設定 TRAVEL_API_URL，請填入已取得授權的旅遊資料 API")
        if not keyword:
            raise ValueError("搜尋關鍵字不可為空")
        limit = max(1, min(int(limit), 100))
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = requests.get(
            self.url,
            params={"q": keyword, "limit": limit},
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            rows = next(
                (payload.get(key) for key in ("data", "results", "items") if isinstance(payload.get(key), list)),
                [],
            )
        else:
            rows = []
        if not isinstance(rows, list):
            raise RuntimeError("授權旅遊 API 回應格式必須是陣列或包含 data/results/items 陣列")
        return [self._normalize(row) for row in rows[:limit] if isinstance(row, dict)]

    @staticmethod
    def _normalize(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": row.get("type", row.get("category", "行程商品")),
            "名稱": row.get("名稱", row.get("name", row.get("title", ""))),
            "縣市": row.get("縣市", row.get("city", row.get("destination", ""))),
            "描述": row.get("描述", row.get("description", row.get("summary", ""))),
            "價格": row.get("價格", row.get("price", "")),
            "網站": row.get("網站", row.get("url", "")),
            "來源": "authorized_api",
        }


class DynamicTravelScraper:
    """以 Selenium 擷取已設定 CSS selector 的動態網站卡片。"""

    def __init__(self, website: str, headless: bool = True, timeout: int = 15):
        if website not in TRAVEL_WEBSITES:
            raise ValueError(f"未設定的網站: {website}")
        self.website = website
        self.config = TRAVEL_WEBSITES[website]
        self.headless = headless
        self.timeout = max(1, int(timeout))

    def search(self, keyword: str, limit: int = 30) -> List[Dict[str, Any]]:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.common.exceptions import TimeoutException

        keyword = str(keyword or "").strip()
        if not keyword:
            raise ValueError("搜尋關鍵字不可為空")
        limit = max(1, min(int(limit), 100))

        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1440,1200")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--lang=zh-TW")
        driver = webdriver.Chrome(options=options)
        try:
            url = self.config["search_url"] + quote_plus(keyword)
            driver.get(url)
            selectors = self.config["selectors"]
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            blocked_markers = ("cloudflare", "access denied", "verify you are human", "驗證您是人類")
            if any(marker in page_text for marker in blocked_markers):
                raise RuntimeError(
                    f"{self.website} 回傳反爬蟲或驗證頁面，未取得商品資料；請使用授權 API、"
                    "可公開存取的資料來源，或在允許自動化存取的環境執行。"
                )
            try:
                cards = WebDriverWait(driver, self.timeout).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selectors["product_cards"]))
                )
            except TimeoutException as error:
                raise RuntimeError(
                    f"{self.website} 在 {self.timeout} 秒內找不到商品 selector "
                    f"'{selectors['product_cards']}'；頁面標題：{driver.title or '無'}"
                ) from error
            results = []
            for card in cards[:limit]:
                results.append({
                    "type": "行程商品",
                    "名稱": self._card_text(card, selectors.get("title"), By),
                    "價格": self._card_text(card, selectors.get("price"), By),
                    "縣市": self._card_text(card, selectors.get("location"), By),
                    "描述": card.text,
                    "網站": driver.current_url,
                    "來源": self.website,
                })
            return results
        finally:
            driver.quit()

    @staticmethod
    def _card_text(card: Any, selector: Optional[str], by: Any) -> str:
        if not selector:
            return ""
        try:
            return card.find_element(by.CSS_SELECTOR, selector).text.strip()
        except Exception:
            return ""


def build_knowledge_base(items: List[Dict[str, Any]], output_path: str = "data/knowledge_base.json") -> Path:
    """輸出 RAG 使用的乾淨資料，保留來源與抓取時間以便追溯。"""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return target