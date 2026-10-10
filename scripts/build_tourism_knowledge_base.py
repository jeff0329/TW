#!/usr/bin/env python3
"""
Build structured place_master, rag_documents, and travel planning corpus
from Tourism Administration V2 open data JSON files.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_ROOT = PROJECT_ROOT / "data" / "raw_tourism_v2"
PROCESSED_ROOT = PROJECT_ROOT / "data" / "processed"


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def pick_first_phone(item: Dict[str, Any]) -> str:
    phones = item.get("Telephones") or []
    if phones and isinstance(phones, list):
        return str(phones[0].get("Tel", ""))
    return ""


def pick_first_image(item: Dict[str, Any]) -> List[str]:
    images = item.get("Images") or []
    urls: List[str] = []
    if isinstance(images, list):
        for img in images[:3]:
            if isinstance(img, dict) and img.get("URL"):
                urls.append(str(img["URL"]))
    return urls


def normalize_place(record: Dict[str, Any], source_type: str) -> Dict[str, Any]:
    source_field_map = {
        "scenic": ("AttractionID", "AttractionName", "AttractionClasses"),
        "restaurant": ("RestaurantID", "RestaurantName", "CuisineClasses"),
        "hotel": ("HotelID", "HotelName", "HotelClasses"),
        "event": ("EventID", "EventName", "EventClasses"),
    }

    id_key, name_key, class_key = source_field_map[source_type]
    addr = record.get("PostalAddress") or {}

    city = str(addr.get("City") or "")
    district = str(addr.get("Town") or "")
    address = str(addr.get("StreetAddress") or "")

    lat = record.get("PositionLat")
    lon = record.get("PositionLon")
    if lat in (None, "") or lon in (None, ""):
        lat, lon = None, None

    desc = str(record.get("Description") or "")
    tags: List[str] = []
    classes = record.get(class_key) or []
    if isinstance(classes, list):
        tags.extend([f"class:{c}" for c in classes[:3]])

    stay_min = 45
    stay_max = 120
    if source_type == "hotel":
        stay_min, stay_max = 720, 960
    elif source_type == "event":
        stay_min, stay_max = 90, 240

    if source_type == "restaurant":
        avg_cost = 450
    elif source_type == "hotel":
        avg_cost = int(record.get("LowestPrice") or 2500)
    elif source_type == "event":
        avg_cost = 200
    else:
        avg_cost = 180

    return {
        "place_id": str(record.get(id_key) or ""),
        "source": "TourismAdministrationOpenData",
        "source_type": source_type,
        "name": str(record.get(name_key) or ""),
        "alias": record.get("AlternateNames") or [],
        "city": city,
        "district": district,
        "address": address,
        "lat": lat,
        "lon": lon,
        "category_lv1": source_type,
        "category_lv2": "",
        "tags": tags,
        "description": desc,
        "intro_short": desc[:160],
        "phone": pick_first_phone(record),
        "website": str(record.get("WebsiteURL") or ""),
        "image_urls": pick_first_image(record),
        "rating": None,
        "review_count": None,
        "price_level": None,
        "avg_cost_twd": avg_cost,
        "stay_minutes_min": stay_min,
        "stay_minutes_max": stay_max,
        "open_hours_text": str(record.get("ServiceTimeInfo") or ""),
        "open_hours_normalized": {},
        "closed_dates": [],
        "suitable_time_slots": ["morning", "afternoon", "evening"],
        "transport_access": {
            "traffic_info": str(record.get("TrafficInfo") or ""),
            "parking_info": str(record.get("ParkingInfo") or ""),
        },
        "data_quality_score": quality_score(city, lat, lon, desc),
        "updated_at": str(record.get("UpdateTime") or datetime.now().isoformat()),
        "raw_payload": record,
    }


def quality_score(city: str, lat: Any, lon: Any, desc: str) -> float:
    score = 0.45
    if city:
        score += 0.15
    if lat not in (None, "") and lon not in (None, ""):
        score += 0.2
    if desc:
        score += 0.2
    return round(min(score, 1.0), 2)


def build_rag_documents(places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for idx, p in enumerate(places):
        text = (
            f"{p['name']} 位於 {p['city']}{p['district']}，類型 {p['source_type']}。"
            f"地址：{p['address']}。"
            f"建議停留 {p['stay_minutes_min']} 到 {p['stay_minutes_max']} 分鐘。"
            f"預估花費 {p['avg_cost_twd']} 元。"
            f"簡介：{p['description'][:220]}"
        )
        docs.append(
            {
                "doc_id": f"DOC-{p['place_id'] or idx}-0",
                "place_id": p["place_id"],
                "chunk_index": 0,
                "chunk_text": text,
                "chunk_tokens_est": max(1, len(text) // 3),
                "lang": "zh-TW",
                "keywords": [p["name"], p["city"], p["source_type"]],
                "embedding_model": "local-hash-1024",
                "embedding_ref": f"local://doc/{p['place_id'] or idx}",
                "freshness_days": 0,
                "source_item": {
                    "name": p["name"],
                    "city": p["city"],
                    "district": p["district"],
                    "source_type": p["source_type"],
                    "description": p["description"],
                    "lat": p["lat"],
                    "lon": p["lon"],
                },
            }
        )
    return docs


def build_training_corpus(places: List[Dict[str, Any]], sample_size: int = 30) -> List[Dict[str, Any]]:
    by_city: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for p in places:
        if p.get("city"):
            by_city[p["city"]].append(p)

    rows: List[Dict[str, Any]] = []
    rng = random.Random(42)

    for city, items in by_city.items():
        scenic = [x for x in items if x["source_type"] in ("scenic", "event")]
        food = [x for x in items if x["source_type"] == "restaurant"]
        hotels = [x for x in items if x["source_type"] == "hotel"]

        if len(scenic) < 2 or len(food) < 1 or len(hotels) < 1:
            continue

        for _ in range(2):
            days = rng.choice([2, 3, 4, 5])
            selected_scenic = rng.sample(scenic, k=min(len(scenic), days + 1))
            selected_food = rng.sample(food, k=min(len(food), days))
            selected_hotels = rng.sample(hotels, k=1)

            budget = (
                sum(x.get("avg_cost_twd") or 0 for x in selected_scenic)
                + sum(x.get("avg_cost_twd") or 0 for x in selected_food)
                + sum((x.get("avg_cost_twd") or 0) * days for x in selected_hotels)
                + days * 300
            )

            geo = [
                {"name": x["name"], "lat": x.get("lat"), "lon": x.get("lon")}
                for x in selected_scenic[:days]
                if x.get("lat") is not None and x.get("lon") is not None
            ]

            rows.append(
                {
                    "destination_city": city,
                    "trip_days": days,
                    "budget_twd": int(budget),
                    "transport_modes": ["捷運", "公車", "步行"],
                    "restaurants": [x["name"] for x in selected_food],
                    "attractions": [x["name"] for x in selected_scenic],
                    "hotels": [x["name"] for x in selected_hotels],
                    "geo_points": geo,
                    "start_spot": selected_scenic[0]["name"],
                    "interests": ["文化", "歷史", "自然"],
                }
            )

    rng.shuffle(rows)
    return rows[:sample_size]


def to_legacy_items(places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    mapping = {
        "scenic": "景點",
        "restaurant": "餐廳",
        "hotel": "飯店",
        "event": "活動",
    }
    legacy: List[Dict[str, Any]] = []
    for p in places:
        legacy.append(
            {
                "type": mapping.get(p["source_type"], p["source_type"]),
                "名稱": p["name"],
                "縣市": p["city"],
                "區域": p["district"],
                "描述": p["description"],
                "地址": p["address"],
                "經度": p["lon"],
                "緯度": p["lat"],
                "電話": p["phone"],
                "網站": p["website"],
                "來源": p["source"],
            }
        )
    return legacy


def main() -> None:
    PROCESSED_ROOT.mkdir(parents=True, exist_ok=True)

    attraction = load_json(RAW_ROOT / "Attraction-json" / "AttractionList.json").get("Attractions", [])
    restaurant = load_json(RAW_ROOT / "Restaurant-json" / "RestaurantList.json").get("Restaurants", [])
    hotel = load_json(RAW_ROOT / "Hotel-json" / "HotelList.json").get("Hotels", [])
    event = load_json(RAW_ROOT / "Event-json" / "EventList.json").get("Events", [])

    places: List[Dict[str, Any]] = []
    places.extend(normalize_place(x, "scenic") for x in attraction)
    places.extend(normalize_place(x, "restaurant") for x in restaurant)
    places.extend(normalize_place(x, "hotel") for x in hotel)
    places.extend(normalize_place(x, "event") for x in event)

    places = [p for p in places if p.get("name") and p.get("city")]

    rag_docs = build_rag_documents(places)
    training = build_training_corpus(places)
    legacy = to_legacy_items(places)

    (PROCESSED_ROOT / "place_master.json").write_text(
        json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (PROCESSED_ROOT / "rag_documents.json").write_text(
        json.dumps(rag_docs, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (PROCESSED_ROOT / "travel_plan_training.json").write_text(
        json.dumps(training, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (PROJECT_ROOT / "data" / f"taiwan_tourism_data_{stamp}.json").write_text(
        json.dumps(legacy, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"places={len(places)}")
    print(f"rag_documents={len(rag_docs)}")
    print(f"training_samples={len(training)}")
    print(f"legacy_export={len(legacy)}")


if __name__ == "__main__":
    main()
