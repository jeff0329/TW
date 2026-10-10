# 旅遊資料庫欄位架構設計（支援 RAG 與行程排程）

## 一、核心設計目標

- 支援 RAG：每筆資料可轉為高品質檢索文本，並保留可追溯來源。
- 支援排程：提供預算、停留時間、開放時段、經緯度等可計算欄位。
- 支援擴充：景點、餐廳、旅宿、活動、交通節點共用主結構。

## 二、建議資料表（或 JSON 物件）結構

### 1. place_master（POI 主檔）

| 欄位 | 型別 | 必填 | 說明 |
|---|---|---|---|
| place_id | string | Y | 全域唯一 ID（例如 `TDX-ScenicSpot-xxxx`） |
| source | string | Y | 資料來源（TDX、觀光署、KKday...） |
| source_type | string | Y | `scenic` / `restaurant` / `hotel` / `activity` / `transport` |
| name | string | Y | 名稱 |
| alias | array[string] | N | 別名、舊稱、英文名 |
| city | string | Y | 縣市 |
| district | string | N | 鄉鎮區 |
| address | string | N | 地址 |
| lat | number | Y | 緯度 |
| lon | number | Y | 經度 |
| category_lv1 | string | Y | 主分類（自然、人文、美食、住宿...） |
| category_lv2 | string | N | 次分類（夜市、博物館、溫泉...） |
| tags | array[string] | N | 標籤（親子、雨天備案、無障礙...） |
| description | string | N | 原始描述 |
| intro_short | string | N | 120~180 字摘要（可預先生成） |
| phone | string | N | 電話 |
| website | string | N | 官網 |
| image_urls | array[string] | N | 圖片連結 |
| rating | number | N | 評分（0~5） |
| review_count | integer | N | 評論數 |
| price_level | integer | N | 價格等級（1~4） |
| avg_cost_twd | integer | N | 平均花費（TWD） |
| stay_minutes_min | integer | Y | 建議停留最短分鐘 |
| stay_minutes_max | integer | Y | 建議停留最長分鐘 |
| open_hours_text | string | N | 原始營業時間字串 |
| open_hours_normalized | object | N | 結構化營業時間（週一到週日） |
| closed_dates | array[string] | N | 特殊休館日期 |
| suitable_time_slots | array[string] | N | `morning`/`afternoon`/`evening`/`night` |
| transport_access | object | N | 最近車站、步行分鐘、停車資訊 |
| data_quality_score | number | Y | 資料完整度（0~1） |
| updated_at | string(datetime) | Y | 最後更新時間 |
| raw_payload | object | N | 原始來源欄位快照 |

### 2. rag_document（檢索文本）

| 欄位 | 型別 | 必填 | 說明 |
|---|---|---|---|
| doc_id | string | Y | 文件 ID |
| place_id | string | Y | 對應 POI |
| chunk_index | integer | Y | 分段索引 |
| chunk_text | string | Y | 向量化文本 |
| chunk_tokens_est | integer | Y | 估算 token 數 |
| lang | string | Y | `zh-TW` / `en` |
| keywords | array[string] | N | 關鍵詞 |
| embedding_model | string | Y | 向量模型名稱 |
| embedding_ref | string | Y | 向量資料庫索引鍵 |
| freshness_days | integer | Y | 距上次更新天數 |

### 3. route_edge（路徑時間/成本矩陣）

| 欄位 | 型別 | 必填 | 說明 |
|---|---|---|---|
| from_place_id | string | Y | 起點 |
| to_place_id | string | Y | 終點 |
| mode | string | Y | `walk` / `bus` / `metro` / `taxi` / `drive` |
| distance_km | number | Y | 距離 |
| duration_min | integer | Y | 預估時間 |
| cost_twd | integer | N | 預估費用 |
| updated_at | string(datetime) | Y | 更新時間 |

### 4. itinerary_constraint_profile（行程約束）

| 欄位 | 型別 | 必填 | 說明 |
|---|---|---|---|
| profile_id | string | Y | 偏好設定 ID |
| total_budget_twd | integer | Y | 總預算 |
| days | integer | Y | 天數 |
| daily_start_time | string | Y | 每日開始時間 |
| daily_end_time | string | Y | 每日結束時間 |
| max_move_minutes_per_day | integer | Y | 每日最大移動時間 |
| preferred_modes | array[string] | N | 偏好交通方式 |
| must_visit_place_ids | array[string] | N | 必去清單 |
| avoid_tags | array[string] | N | 排除標籤 |

## 三、結構化示範種子資料（JSON）

- 檔案位置：[data/seed_tourism_sample.json](data/seed_tourism_sample.json)
- 包含 `places`、`rag_documents`、`route_edges`、`constraint_profile_example` 四塊。
- 可直接作為 RAG 建索引與排程演算法測試輸入。

## 四、資料來源安排

### 1. 景點、餐廳、住宿、活動（優先來源）

優先使用交通部觀光署的觀光資訊資料庫：

- 景點資料：https://data.gov.tw/dataset/7777
- 同系列另有餐飲、旅宿及活動資料集
- 支援 JSON / XML 格式
- 具固定更新頻率（以各資料集公告為準）
- 通常包含座標、地址、營業資訊、票價、交通、停車、圖片、建議停留時間等欄位

為何優先採用政府資料：

- 法務風險較低：授權條款清楚，適合學術研究與系統開發。
- 品質穩定：欄位規格一致性高，便於建立 ETL 與排程更新流程。
- 可追溯性高：來源明確，適合寫入研究方法與資料治理章節。

與商業網站爬蟲（如地圖、評論、訂房站）相比，政府開放資料通常更安全、更適合納入研究計畫的資料蒐集方法。建議將商業網站資料定位為「補充來源」，僅在授權允許且必要時使用。

### 2. 來源優先級與資料治理（建議）

1. 第一優先：交通部觀光署 / data.gov.tw / TDX 官方 API。
2. 第二優先：合法授權之平台 API 或合作資料。
3. 第三優先：合規爬蟲補洞（僅補缺欄位，不覆蓋核心欄位）。

欄位採信原則：

- 核心欄位（名稱、座標、地址、開放資訊）優先採官方來源。
- 商業來源僅補充價格、熱門度、評論趨勢等衍生欄位。
- 所有資料保留 `source`、`updated_at`、`raw_payload` 以利稽核。

## 五、取得海量資料（數萬筆）的 3 大實作途徑

### 途徑 1：政府開放資料平臺（最穩定、免爬蟲、資料量龐大）

- 交通部觀光署資料：景點、合法旅宿、餐飲，欄位完整且更新穩定。
- TDX API：可用 RESTful 方式批次擷取觀光與交通站點。
- 優點：品質高、來源可信、法務風險低。
- 風險：欄位在不同資料集命名不一致，需正規化。

建議流程：
1. 先做全量抓取（bootstrap）。
2. 建立每週增量更新（依更新時間或快照 diff）。
3. 將原始欄位映射到 `place_master`，保留 `raw_payload`。

### 途徑 2：平台 API/合作資料（半結構化，高商業價值）

- 來源如訂房/票券/評論平台的公開 API 或合作資料匯出。
- 補足政府資料欠缺的價格、即時營業資訊、熱門度。
- 優點：更貼近旅遊決策所需（預算、可訂性、熱度）。
- 風險：授權、速率限制、資料格式異動。

建議流程：
1. 分來源建立 connector。
2. 將價格與評分做標準化（幣別、分數尺度）。
3. 用 `source_priority` 決定多來源衝突欄位採信規則。

### 途徑 3：網頁爬蟲補洞（彈性高，僅補缺）

- 針對 API 缺漏欄位（例如票價區間、季節資訊、注意事項）做目標型爬取。
- 優點：可快速補齊特定欄位。
- 風險：反爬、網站條款、維護成本高。

建議流程：
1. 先靠途徑 1/2 建主體資料。
2. 只針對缺漏欄位啟動爬蟲，減少法律與維運風險。
3. 爬回資料只做「補充欄位」，不可覆蓋高可信來源核心欄位。

## 六、Python 爬蟲批次抓取與資料清洗（對應研究步驟）

### 批次 Pipeline（建議）

1. Extract：批次抓取 TDX/開放資料/API。
2. Normalize：欄位映射、型別轉換（lat/lon、price、duration）。
3. Validate：必填欄位檢查與座標範圍檢查。
4. Deduplicate：以 `name + city + geo hash` 去重。
5. Enrich：產生 `intro_short`、`tags`、`open_hours_normalized`。
6. Chunking：輸出 RAG chunk 到 `rag_document`。
7. Export：寫入 JSON/CSV/DB，建立版本號。

### 建議指令（以現有專案）

```bash
# 1) 先抓官方資料
python -m backend.scraper

# 2) 再抓平台補充資料（範例）
python scripts/taiwan1.py

# 3) 最後執行清洗與整併（可新增 normalize script）
python scripts/Taiwan.py
```

## 七、最小品質門檻（建議）

- `name/city/lat/lon/source/source_type` 缺一不可。
- `stay_minutes_min`、`stay_minutes_max` 必須為正整數，且 `min <= max`。
- `avg_cost_twd` 缺值可為 `null`，但不可為負值。
- 座標範圍檢查：`21 <= lat <= 26.5`、`119 <= lon <= 123.5`（台灣範圍近似）。
- `data_quality_score < 0.6` 的資料不進入預設檢索集。
