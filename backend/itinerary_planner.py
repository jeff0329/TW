"""以 place_master（政府觀光開放資料正規化後的 POI 主檔）為基礎的
行程規劃演算法。

對應專題核心訴求：
1. 預算控制：以 avg_cost_twd 逐站累計花費，超出預算上限時自動降級/替換。
2. 天數安排：依天數展開每日時段（上午景點／午餐／下午景點／晚餐／住宿）。
3. 動線順暢度：以經緯度做最近鄰排序，降低同日站點間的移動距離。
4. 多元主題推薦：依描述關鍵字推斷主題標籤，跨日/跨時段輪替主題並可依使用者興趣加權。

僅回傳可由既有資料驗證的結構化行程；文字敘述交由 LLM 依此結構生成，
避免模型自行虛構景點或價格（降低 AI 幻覺風險）。
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLACE_MASTER_PATH = PROJECT_ROOT / "data" / "processed" / "place_master.json"

MIN_QUALITY_SCORE = 0.55
MIN_POOL_SIZE = 3
FALLBACK_RADIUS_KM = 60.0

# 依名稱/描述關鍵字粗略推斷「多元主題」標籤，供跨日主題輪替與興趣比對使用。
THEME_KEYWORDS = {
    "自然生態": ["國家公園", "步道", "瀑布", "溫泉", "湖", "森林", "海岸", "海灘", "山", "生態", "自然"],
    "歷史古蹟": ["古蹟", "古城", "遺址", "廟", "宮", "寺", "歷史", "文物", "城"],
    "文化藝術": ["博物館", "美術館", "文創", "藝術", "展覽", "文化園區", "老街"],
    "夜市美食": ["夜市", "小吃", "美食街"],
    "休閒放鬆": ["公園", "商圈", "夜景", "纜車", "遊樂"],
}


def infer_theme(place: Dict[str, Any]) -> str:
    source_type = place.get("source_type")
    if source_type == "restaurant":
        return "美食"
    if source_type == "hotel":
        return "住宿"
    if source_type == "event":
        return "活動慶典"
    text = f"{place.get('name', '')} {place.get('description', '')[:120]}"
    for theme, keywords in THEME_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return theme
    return "自然人文"


def _normalize_city(text: str) -> str:
    text = str(text or "").strip()
    return text.replace("台", "臺").replace("縣", "").replace("市", "")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(min(1.0, math.sqrt(a)))


class PlaceIndex:
    """place_master.json 的輕量記憶體索引（去除大型欄位以節省記憶體）。"""

    _instance: Optional["PlaceIndex"] = None

    def __init__(self, places: List[Dict[str, Any]]):
        self.places = places
        self.city_index: Dict[str, List[int]] = {}
        for idx, place in enumerate(places):
            key = _normalize_city(place.get("city", ""))
            if key:
                self.city_index.setdefault(key, []).append(idx)

    @classmethod
    def load(cls) -> "PlaceIndex":
        if cls._instance is not None:
            return cls._instance
        places: List[Dict[str, Any]] = []
        if PLACE_MASTER_PATH.exists():
            try:
                raw = json.loads(PLACE_MASTER_PATH.read_text(encoding="utf-8"))
                for record in raw:
                    places.append({
                        "place_id": record.get("place_id"),
                        "source": record.get("source"),
                        "source_type": record.get("source_type"),
                        "name": record.get("name"),
                        "city": record.get("city"),
                        "district": record.get("district"),
                        "address": record.get("address"),
                        "lat": record.get("lat"),
                        "lon": record.get("lon"),
                        "tags": record.get("tags") or [],
                        "description": (record.get("description") or "")[:200],
                        "avg_cost_twd": record.get("avg_cost_twd") or 0,
                        "stay_minutes_min": record.get("stay_minutes_min") or 60,
                        "stay_minutes_max": record.get("stay_minutes_max") or 120,
                        "data_quality_score": record.get("data_quality_score") or 0,
                        "rating": record.get("rating"),
                    })
            except (OSError, json.JSONDecodeError):
                logger.exception("無法載入 place_master.json")
        cls._instance = cls(places)
        return cls._instance

    def find_candidates(self, destination: str) -> List[Dict[str, Any]]:
        target = _normalize_city(destination)
        if not target:
            return []
        indices: List[int] = []
        for city_key, idx_list in self.city_index.items():
            if target in city_key or city_key in target:
                indices.extend(idx_list)
        if not indices:
            # 退而求其次：以景點/區域名稱做包含比對
            compact_target = target
            for idx, place in enumerate(self.places):
                haystack = f"{place.get('district', '')}{place.get('name', '')}"
                if compact_target and compact_target in _normalize_city(haystack):
                    indices.append(idx)
        candidates = [self.places[i] for i in indices]
        return [p for p in candidates if (p.get("data_quality_score") or 0) >= MIN_QUALITY_SCORE]


def _broaden_pool_if_needed(pool: List[Dict[str, Any]], source_types: Tuple[str, ...],
                             anchor: Tuple[float, float], index: "PlaceIndex", destination_city: str = "") -> List[Dict[str, Any]]:
    """部分縣市之開放資料在特定類別（如餐飲）收錄量偏低時，
    放寬到鄰近地區（以錨點直線距離 FALLBACK_RADIUS_KM 內）以維持行程完整性。"""
    if len(pool) >= MIN_POOL_SIZE:
        return pool
    existing_ids = {p.get("place_id") for p in pool}
    allowed_cities = {_normalize_city(destination_city)} if destination_city else {
        _normalize_city(p.get("city", ""))
        for p in pool
        if _normalize_city(p.get("city", ""))
    }
    nearby = []
    for place in index.places:
        if place.get("source_type") not in source_types:
            continue
        # ????????????????????????
        place_city = _normalize_city(place.get("city", ""))
        if allowed_cities and place_city not in allowed_cities:
            continue
        if place.get("place_id") in existing_ids:
            continue
        if (place.get("data_quality_score") or 0) < MIN_QUALITY_SCORE:
            continue
        lat, lon = place.get("lat"), place.get("lon")
        if lat is None or lon is None:
            continue
        if haversine_km(anchor[0], anchor[1], lat, lon) <= FALLBACK_RADIUS_KM:
            nearby.append(place)
    return pool + nearby


def _pick_nearest(pool: List[Dict[str, Any]], anchor: Tuple[float, float], used: set,
                   preferred_themes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """從候選池挑選離錨點最近、且未使用過的地點；優先符合興趣主題。"""
    best = None
    best_score = None
    for place in pool:
        pid = place.get("place_id")
        name_key = f"name::{str(place.get('name') or '').strip()}"
        if not pid or pid in used or name_key in used:
            continue
        lat, lon = place.get("lat"), place.get("lon")
        if lat is None or lon is None:
            distance = 999.0
        else:
            distance = haversine_km(anchor[0], anchor[1], lat, lon)
        theme_bonus = 0.0
        if preferred_themes and infer_theme(place) in preferred_themes:
            theme_bonus = -5.0  # 距離分數越低越好，符合興趣時給予加權優先
        score = distance + theme_bonus
        if best_score is None or score < best_score:
            best_score = score
            best = place
    return best


def _mark_used(used: set, place: Dict[str, Any]) -> None:
    used.add(place.get("place_id"))
    used.add(f"name::{str(place.get('name') or '').strip()}")


def _unmark_used(used: set, place: Dict[str, Any]) -> None:
    used.discard(place.get("place_id"))
    used.discard(f"name::{str(place.get('name') or '').strip()}")


def _slot_time(hour: int, minute: int = 0) -> str:
    return f"{hour:02d}:{minute:02d}"


# 對應前端「旅遊節奏」選項：packed=緊湊充實(6-7點/日)、moderate=適中節奏(4-5點/日)、leisurely=悠閒慢遊(3-4點/日)
PACE_SLOT_CONFIG = {
    "packed": {"morning": 2, "afternoon": 2, "meals": 2},
    "moderate": {"morning": 1, "afternoon": 1, "meals": 2},
    "leisurely": {"morning": 1, "afternoon": 1, "meals": 1},
}


def _transit_descriptor(distance_km: float) -> Dict[str, Any]:
    """依直線距離概估交通方式/時間/費用（僅供顯示參考，非即時routing）。"""
    if distance_km <= 1.2:
        minutes = max(3, round(distance_km / 4 * 60))
        return {"mode": "步行", "time": f"{minutes} 分", "cost": 0}
    if distance_km <= 6:
        minutes = max(5, round(distance_km / 18 * 60))
        return {"mode": "公車", "time": f"{minutes} 分", "cost": round(15 + distance_km * 3)}
    if distance_km <= 15:
        minutes = max(8, round(distance_km / 25 * 60))
        return {"mode": "捷運/公車", "time": f"{minutes} 分", "cost": round(20 + distance_km * 3)}
    minutes = max(15, round(distance_km / 45 * 60))
    return {"mode": "客運/火車", "time": f"{minutes} 分", "cost": round(50 + distance_km * 4)}


def _attach_transit(day_stops: List[Dict[str, Any]]) -> None:
    """為每一站附上前往下一站的交通資訊（供前端時間軸顯示）。"""
    for current, nxt in zip(day_stops, day_stops[1:]):
        if current.get("lat") is not None and nxt.get("lat") is not None:
            distance = haversine_km(current["lat"], current["lon"], nxt["lat"], nxt["lon"])
            current["transit"] = _transit_descriptor(distance)
        else:
            current["transit"] = {"mode": "大眾運輸", "time": "-", "cost": 0}


def build_itinerary(destination: str, days: int, budget: float, interests: Optional[List[str]] = None,
                     pace: str = "moderate") -> Dict[str, Any]:
    """依預算上限、天數、興趣與旅遊節奏，產生可驗證的結構化行程。"""
    interests = [str(i).strip() for i in (interests or []) if str(i).strip()]
    pace_config = PACE_SLOT_CONFIG.get(pace, PACE_SLOT_CONFIG["moderate"])
    index = PlaceIndex.load()
    candidates = index.find_candidates(destination)

    if not candidates:
        return {
            "destination": destination,
            "days_count": days,
            "budget_cap": budget,
            "estimated_total": 0,
            "remaining_budget": budget,
            "compliant": None,
            "themes_covered": [],
            "route_smoothness_km": None,
            "days": [],
            "data_grounded": False,
        }

    scenic_pool = [p for p in candidates if p.get("source_type") in ("scenic", "event")]
    food_pool = [p for p in candidates if p.get("source_type") == "restaurant"]
    hotel_pool = [p for p in candidates if p.get("source_type") == "hotel"]

    lats = [p["lat"] for p in candidates if p.get("lat") is not None]
    lons = [p["lon"] for p in candidates if p.get("lon") is not None]
    anchor = (sum(lats) / len(lats), sum(lons) / len(lons)) if lats and lons else (23.7, 121.0)

    # 政府開放資料部分縣市之特定類別（例如餐飲）收錄量偏低，
    # 若同縣市內某類別候選不足，放寬至鄰近地區（以直線距離為準）以維持行程完整性。
    scenic_pool = _broaden_pool_if_needed(scenic_pool, ("scenic", "event"), anchor, index, destination)
    food_pool = _broaden_pool_if_needed(food_pool, ("restaurant",), anchor, index, destination)
    hotel_pool = _broaden_pool_if_needed(hotel_pool, ("hotel",), anchor, index, destination)

    used: set = set()
    day_plans: List[List[Dict[str, Any]]] = []
    theme_rotation = list(THEME_KEYWORDS.keys())

    for day_idx in range(days):
        day_stops: List[Dict[str, Any]] = []
        day_anchor = anchor if day_idx == 0 else (
            day_plans[-1][-1]["lat"], day_plans[-1][-1]["lon"]
        ) if day_plans and day_plans[-1] and day_plans[-1][-1].get("lat") is not None else anchor

        last_theme = None
        clock_minutes = 9 * 60

        # 上午景點（依節奏可為 1~2 個），優先符合使用者興趣，其次依主題輪替確保多元主題
        for slot_idx in range(pace_config["morning"]):
            theme_pref = interests or [theme_rotation[(day_idx + slot_idx) % len(theme_rotation)]]
            pick = _pick_nearest(scenic_pool, day_anchor, used, theme_pref)
            if not pick:
                break
            _mark_used(used, pick)
            last_theme = infer_theme(pick)
            day_stops.append({**pick, "time": _slot_time(clock_minutes // 60, clock_minutes % 60), "theme": last_theme})
            day_anchor = (pick.get("lat") or day_anchor[0], pick.get("lon") or day_anchor[1])
            clock_minutes += 120

        if pace_config["meals"] >= 1:
            clock_minutes = max(clock_minutes, 12 * 60)
            lunch = _pick_nearest(food_pool, day_anchor, used)
            if lunch:
                _mark_used(used, lunch)
                day_stops.append({**lunch, "time": _slot_time(clock_minutes // 60, clock_minutes % 60), "theme": infer_theme(lunch)})
                day_anchor = (lunch.get("lat") or day_anchor[0], lunch.get("lon") or day_anchor[1])
                clock_minutes += 90

        # 下午景點：主題與上午最後一站不同，確保同一天內也有多元主題
        clock_minutes = max(clock_minutes, 14 * 60)
        for slot_idx in range(pace_config["afternoon"]):
            theme_pref = [t for t in theme_rotation if t != last_theme]
            pick = _pick_nearest(scenic_pool, day_anchor, used, theme_pref)
            if not pick:
                break
            _mark_used(used, pick)
            last_theme = infer_theme(pick)
            day_stops.append({**pick, "time": _slot_time(clock_minutes // 60, clock_minutes % 60), "theme": last_theme})
            day_anchor = (pick.get("lat") or day_anchor[0], pick.get("lon") or day_anchor[1])
            clock_minutes += 120

        if pace_config["meals"] >= 2:
            clock_minutes = max(clock_minutes, 18 * 60)
            dinner = _pick_nearest(food_pool, day_anchor, used)
            if dinner:
                _mark_used(used, dinner)
                day_stops.append({**dinner, "time": _slot_time(clock_minutes // 60, clock_minutes % 60), "theme": infer_theme(dinner)})
                day_anchor = (dinner.get("lat") or day_anchor[0], dinner.get("lon") or day_anchor[1])

        if day_idx < days - 1 and hotel_pool:
            hotel = _pick_nearest(hotel_pool, day_anchor, used)
            if hotel:
                _mark_used(used, hotel)
                day_stops.append({**hotel, "time": _slot_time(21, 30), "theme": "住宿"})

        day_plans.append(day_stops)

    total, day_plans = _enforce_budget(day_plans, budget, scenic_pool, food_pool, hotel_pool, used)
    for day_stops in day_plans:
        _attach_transit(day_stops)
    route_smoothness = _average_route_distance(day_plans)
    themes_covered = sorted({stop["theme"] for day in day_plans for stop in day})

    return {
        "destination": destination,
        "days_count": days,
        "budget_cap": budget,
        "estimated_total": round(total, 0),
        "remaining_budget": round(budget - total, 0),
        "compliant": total <= budget,
        "themes_covered": themes_covered,
        "route_smoothness_km": route_smoothness,
        "days": day_plans,
        "data_grounded": True,
    }


def _stop_cost(stop: Dict[str, Any]) -> float:
    return float(stop.get("avg_cost_twd") or 0)


def _transport_cost(day: List[Dict[str, Any]]) -> float:
    """以相鄰站點距離概估交通費（每公里約 15 元），呼應 route_edge 概念。"""
    cost = 0.0
    for a, b in zip(day, day[1:]):
        if a.get("lat") is not None and b.get("lat") is not None:
            cost += haversine_km(a["lat"], a["lon"], b["lat"], b["lon"]) * 15
    return cost


def _day_total(day: List[Dict[str, Any]]) -> float:
    return sum(_stop_cost(stop) for stop in day) + _transport_cost(day)


def _enforce_budget(day_plans: List[List[Dict[str, Any]]], budget: float,
                     scenic_pool: List[Dict[str, Any]], food_pool: List[Dict[str, Any]],
                     hotel_pool: List[Dict[str, Any]], used: set,
                     max_iterations: int = 300) -> Tuple[float, List[List[Dict[str, Any]]]]:
    """超出預算時，優先以同主題/同類別較便宜的候選替換花費最高的站點（包含住宿），若無候補才移除。"""
    total = sum(_day_total(day) for day in day_plans)
    iterations = 0
    pool_by_type = {"scenic": scenic_pool, "event": scenic_pool, "restaurant": food_pool, "hotel": hotel_pool}
    while total > budget and iterations < max_iterations:
        iterations += 1
        # 找出所有站點中花費最高者（住宿也可被降級/替換）
        priciest = None
        priciest_loc = None
        for d_idx, day in enumerate(day_plans):
            for s_idx, stop in enumerate(day):
                if priciest is None or _stop_cost(stop) > _stop_cost(priciest):
                    priciest = stop
                    priciest_loc = (d_idx, s_idx)
        if priciest is None or priciest_loc is None or _stop_cost(priciest) <= 0:
            break

        d_idx, s_idx = priciest_loc
        pool = pool_by_type.get(priciest.get("source_type"), scenic_pool)
        cheaper_alt = None
        for candidate in pool:
            pid = candidate.get("place_id")
            name_key = f"name::{str(candidate.get('name') or '').strip()}"
            if not pid or pid in used or name_key in used:
                continue
            if _stop_cost(candidate) < _stop_cost(priciest):
                if cheaper_alt is None or _stop_cost(candidate) < _stop_cost(cheaper_alt):
                    cheaper_alt = candidate

        if cheaper_alt is not None:
            _unmark_used(used, priciest)
            _mark_used(used, cheaper_alt)
            theme = "住宿" if cheaper_alt.get("source_type") == "hotel" else infer_theme(cheaper_alt)
            day_plans[d_idx][s_idx] = {**cheaper_alt, "time": priciest["time"], "theme": theme}
        else:
            _unmark_used(used, priciest)
            del day_plans[d_idx][s_idx]

        total = sum(_day_total(day) for day in day_plans)

    return total, day_plans


def _average_route_distance(day_plans: List[List[Dict[str, Any]]]) -> Optional[float]:
    distances = []
    for day in day_plans:
        for a, b in zip(day, day[1:]):
            if a.get("lat") is not None and b.get("lat") is not None:
                distances.append(haversine_km(a["lat"], a["lon"], b["lat"], b["lon"]))
    if not distances:
        return None
    return round(sum(distances) / len(distances), 2)


def flatten_recommended_places(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """去重後攤平所有已選景點/餐廳/住宿，供前端 recommended_places 使用。"""
    seen = set()
    flat: List[Dict[str, Any]] = []
    for day in result.get("days", []):
        for stop in day:
            pid = stop.get("place_id")
            if pid in seen:
                continue
            seen.add(pid)
            flat.append(stop)
    return flat
