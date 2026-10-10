# 🗺️ 台灣旅遊規劃助手

由 AI 驅動的智慧旅遊規劃平台 - 使用 Ollama 本地 LLM + 旅遊數據 + RAG 架構

## 📋 項目概述

這是一個完整的台灣旅遊規劃系統，整合了：

## 🚀 快速開始

### 前置需求


### 4.1 建立本地知識庫

TDX 資料會先經過欄位統一、空白清理與 `(類型, 名稱, 縣市)` 去重，再由 RAG 建立本地索引。也可以用經授權的動態網站擷取器：

```bash
python -c "from data_pipeline import DynamicTravelScraper, TourismDataPipeline; p=TourismDataPipeline(); rows=p.clean(DynamicTravelScraper('kkday').search('台北')); print(p.quality_report(rows)); p.save(rows)"
```

動態網站擷取需遵守網站服務條款、robots.txt、請求頻率限制與個人資料保護規範。

## 🧪 資料與模型評估 API

```http
GET  /api/data/quality
POST /api/scrape/dynamic
POST /api/evaluate/retrieval
POST /api/evaluate/plan
```

`/api/evaluate/retrieval` 的 request body 範例：

```json
{
  "top_k": 5,
  "cases": [
    {"query": "台北 美食", "expected_names": ["台北101", "士林夜市"]}
  ]
}
```

`/api/evaluate/plan` 會檢查行程是否包含景點、餐廳、交通、預算段落，並從文字中的「預算總計」計算預算符合率。無法從模型文字辨識總額時會回報 `null`，不會誤判為通過。
- Ollama（本地 LLM 框架）
- 4GB+ RAM（推薦 8GB+）
- 網絡連接（用於首次數據爬取和 API 調用）

### 1. 安裝 Ollama

從 [ollama.com](https://ollama.com) 下載並安裝 Ollama

### 2. 下載並啟動 LLM 模型

```bash
# 啟動 Ollama 服務
ollama serve

# 在另一個終端，下載模型（首次執行）
ollama pull llama2          # 推薦 (4GB)
# 或
ollama pull mistral         # 更輕量 (3.8GB)
# 或
ollama pull neural-chat     # 中文優化 (3.8GB)
```

### 1.1 設定 TDX 與授權旅遊 API

TDX 是本專案的主要資料來源。請至 TDX 平台申請 App ID 與 App Key，並在 PowerShell 設定環境變數：

```powershell
$env:TDX_APP_ID = "你的 TDX App ID"
$env:TDX_APP_KEY = "你的 TDX App Key"
```

若有其他已取得授權的旅遊資料 API，可設定：

```powershell
$env:TRAVEL_API_URL = "https://example.com/api/travel/search"
$env:TRAVEL_API_KEY = "你的 API Key"
```

也可透過 `POST /api/scrape/authorized` 傳入 `url`、`api_key`、`keyword` 與 `limit`。API 回應需為陣列，或包含 `data`、`results`、`items` 其中之一的 JSON 物件。

### 1.2 執行本地 Selenium 測試

此測試頁由 JavaScript 動態插入第三筆商品，不依賴 KKday、Klook 等第三方網站：

```powershell
python tests/test_selenium_fixture.py
```

### 3. 安裝 Python 依賴

```bash
# 創建虛擬環境（可選但推薦）
python -m venv venv
source venv/Scripts/activate  # Windows
# 或
source venv/bin/activate  # Linux/Mac

# 安裝依賴
pip install -r requirements.txt
```

### 4. 收集旅遊數據

```bash
# 執行爬蟲，從 TDX API 收集數據
python scraper.py
```

輸出：
- `data/scenic_spots.json` - 景點數據
- `data/restaurants.json` - 餐廳數據
- `data/hotels.json` - 飯店數據
- `data/taiwan_tourism_data.json` - 合併數據

### 5. 啟動 Web 應用

```bash
# 運行 Flask 服務器
python app.py
```

訪問：http://localhost:5000

## 📁 項目結構

```
Taiwan/
├── config.py                    # 配置文件
├── scraper.py                   # 網路爬蟲模組
├── ollama_integration.py         # Ollama 集成和 RAG
├── app.py                        # Flask API 伺服器
├── requirements.txt              # Python 依賴
├── README.md                     # 本說明文檔
├── templates/
│   └── index.html               # 前端 HTML
├── static/
│   ├── style.css                # 樣式表
│   └── script.js                # 交互腳本
├── data/                         # 數據存儲目錄
│   ├── scenic_spots.json
│   ├── restaurants.json
│   └── hotels.json
└── logs/
    └── scraper.log              # 日誌文件
```

## 🎯 主要功能

### 1. 智慧行程規劃
- 基於預算和興趣自動生成行程
- 包含景點、餐廳、飯店和交通建議
- 支援自訂修改

### 2. 數據搜尋
- 搜尋景點、餐廳、飯店
- 按地區和類別篩選
- 展示詳細信息

### 3. 目的地信息
- 獲取城市概況
- 推薦景點和美食
- 旅遊貼士

### 4. 行程管理
- 保存已生成的行程
- 導出 PDF/Excel（開發中）
- 分享行程到社交媒體

## 🔌 API 文檔

### 基础 URL
```
http://localhost:5000/api
```

### 端點

#### 1. 健康檢查
```http
GET /health
```

響應：
```json
{
  "status": "ok",
  "timestamp": "2026-05-07T10:00:00",
  "data_loaded": true,
  "planner_ready": true
}
```

#### 2. 數據統計
```http
GET /data/summary
```

響應：
```json
{
  "total_items": 5000,
  "types": {
    "景點": 2000,
    "餐廳": 2000,
    "飯店": 1000
  },
  "locations": ["台北", "高雄", "...]
}
```

#### 3. 搜尋
```http
GET /search?q=keyword&location=台北&type=景點
```

參數：
- `q` (必須) - 搜尋關鍵字
- `location` (可選) - 縣市名稱
- `type` (可選) - 類型（景點/餐廳/飯店）

#### 4. 生成行程
```http
POST /plan/generate
Content-Type: application/json

{
  "destination": "台北",
  "days": 3,
  "budget": 10000,
  "interests": ["文化", "美食"]
}
```

響應：
```json
{
  "status": "success",
  "itinerary": {
    "destination": "台北",
    "days": 3,
    "budget": 10000,
    "plan": "行程內容...",
    "recommended_places": [...]
  }
}
```

#### 5. 獲取所有位置
```http
GET /locations
```

#### 6. 目的地詳情
```http
GET /destination/台北
```

#### 7. 手動執行爬蟲
```http
POST /scrape/tdx
```

## 🤖 Ollama 模型選擇

### 推薦配置

| 模型 | 大小 | 記憶體需求 | 速度 | 中文支持 | 用途 |
|------|------|----------|------|--------|------|
| llama2 | 4GB | 8GB | 中等 | 一般 | 通用 |
| mistral | 3.8GB | 8GB | 快 | 一般 | 快速回應 |
| neural-chat | 3.8GB | 8GB | 快 | 優秀 | 聊天對話 |
| qwen | 3.8GB | 8GB | 快 | 優秀 | 中文優化 |

### 切換模型

編輯 `config.py`：
```python
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "model": "mistral",  # 改為你想使用的模型
    ...
}
```

## 📊 數據來源

### TDX 交通部開放數據
- 景點資訊（Attraction，觀光 OAS V2）
- 餐廳資訊（Restaurant）
- 飯店資訊（Hotel）
- 活動資訊（Activity）

### 支持的旅遊網站
- KKday
- Klook
- Viator
- (可添加更多)

## 🔧 配置調整

編輯 `config.py` 可修改：

```python
# TDX 設置
TDX_CONFIG = {
    "top_limit": 5000  # 每次查詢最多筆數
}

# Ollama 設置
OLLAMA_CONFIG = {
    "model": "llama2",
    "temperature": 0.7,  # 創意程度 (0-1)
    "top_k": 40,
    "top_p": 0.9
}

# RAG 設置
RAG_CONFIG = {
    "chunk_size": 500,
    "chunk_overlap": 100,
    "similarity_threshold": 0.7
}
```

## 🐛 故障排查

### 無法連接到 Ollama
```
❌ 無法連接到 Ollama：Cannot connect
```

**解決方案：**
```bash
# 1. 確保 Ollama 已啟動
ollama serve

# 2. 檢查默認地址（應為 http://localhost:11434）
curl http://localhost:11434/api/tags

# 3. 檢查防火牆設置
```

### 沒有數據可用
```
⚠️ 數據目錄不存在或為空
```

**解決方案：**
```bash
# 執行爬蟲收集數據
python scraper.py

# 或使用 API 手動觸發
curl -X POST http://localhost:5000/api/scrape/tdx
```

### 行程生成很慢
**原因：** 模型太大或硬體不足

**解決方案：**
1. 切換到更輕量的模型（mistral 或 neural-chat）
2. 增加系統 RAM
3. 確保 GPU 加速已啟用

## 📈 性能優化

### 1. GPU 加速
Ollama 支援多種 GPU：
- NVIDIA CUDA
- AMD ROCm
- Apple Metal (M1/M2)

確認設置：
```bash
ollama show model_name
# 查看 "parameters: stop" 後的輸出，確認 GPU 使用
```

### 2. 向量數據庫優化
目前使用簡化的相似度計算，可升級為：
- Faiss（Facebook AI 向量檢索）
- Milvus（開源向量數據庫）
- Weaviate

### 3. 快取機制
實現請求快取減少重複計算

## 🔐 安全性考慮

- ✅ 數據完全在本地處理
- ✅ 沒有數據發送到第三方服務
- ✅ 支持 HTTPS（生產環境推薦）
- ⚠️ 生產環境請添加身份驗證

## 📝 使用示例

### 使用 Python 調用

```python
from ollama_integration import initialize_system

# 初始化系統
planner = initialize_system('./data/taiwan_tourism_data.json')

# 規劃行程
itinerary = planner.plan_itinerary(
    destination="台北",
    days=3,
    budget=5000,
    interests=["文化", "美食", "夜生活"]
)

print(itinerary['plan'])
```

### 使用 cURL 調用 API

```bash
# 生成行程
curl -X POST http://localhost:5000/api/plan/generate \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "台北",
    "days": 3,
    "budget": 10000,
    "interests": ["文化", "美食"]
  }'
```

## 🤝 貢獻指南

歡迎提交 Pull Request 或報告 Issue！

### 改進方向
- [ ] 支援更多旅遊網站爬蟲
- [ ] 實現用戶帳戶系統
- [ ] 添加行程分享和協作功能
- [ ] 支援多語言
- [ ] 移動應用版本
- [ ] 實時票卷預訂整合

## 📄 許可證

MIT License - 自由使用和修改

## 📞 聯繫方式

- 問題報告：GitHub Issues
- 功能建議：GitHub Discussions
- 學術合作：聯絡專題指導教授

## 🙏 致謝

- 交通部 TDX 開放數據平台
- Ollama 開源項目
- Flask 框架
- 所有貢獻者

---

**最後更新：** 2026 年 5 月 7 日  
**版本：** 1.0.0  
**作者：** 台灣旅遊規劃研究團隊
