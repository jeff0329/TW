import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source_path = root / "data" / "knowledge_base.json"
output_path = root / "data" / "processed" / "place_master.json"

type_map = {
    "景點": "scenic",
    "餐廳": "restaurant",
    "飯店": "hotel",
    "活動": "event",
}

stay_map = {
    "景點": (60, 180),
    "餐廳": (60, 90),
    "飯店": (600, 900),
    "活動": (60, 180),
}

with source_path.open("r", encoding="utf-8") as f:
    raw = json.load(f)

places = []
skipped = 0

for i, r in enumerate(raw, start=1):
    kind = str(r.get("type") or "").strip()
    name = str(r.get("名稱") or "").strip()
    city = str(r.get("縣市") or "").strip()
    description = str(r.get("描述") or "").strip()

    if kind not in type_map or not name or not city:
        skipped += 1
        continue

    lat = r.get("緯度")
    lon = r.get("經度")

    if lat is None or lon is None:
        skipped += 1
        continue

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        skipped += 1
        continue

    quality = 0.45
    quality += 0.15 if city else 0
    quality += 0.20
    quality += 0.20 if description else 0

    stay_min, stay_max = stay_map[kind]

    places.append({
        "place_id": f"tourism_{i:06d}",
        "source": r.get("來源") or "TourismAdministrationOpenData",
        "source_type": type_map[kind],
        "name": name,
        "city": city,
        "district": r.get("區域") or "",
        "address": r.get("地址") or "",
        "lat": lat,
        "lon": lon,
        "tags": [kind] + ([r["分類"]] if r.get("分類") else []),
        "description": description[:200],
        "avg_cost_twd": 0,
        "stay_minutes_min": stay_min,
        "stay_minutes_max": stay_max,
        "data_quality_score": round(quality, 2),
        "rating": None,
        "phone": r.get("電話") or "",
        "website": r.get("網站") or "",
    })

output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w", encoding="utf-8") as f:
    json.dump(places, f, ensure_ascii=False, indent=2)

print(f"原始筆數：{len(raw)}")
print(f"轉換筆數：{len(places)}")
print(f"略過筆數：{skipped}")
print(f"輸出檔案：{output_path}")

print("各類型筆數：")
for kind in type_map.values():
    count = sum(p["source_type"] == kind for p in places)
    print(f"  {kind}: {count}")

print(
    "品質分數低於 0.55："
    f"{sum(p['data_quality_score'] < 0.55 for p in places)}"
)
