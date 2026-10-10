# 📚 項目架構與設計

## 系統架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                     用戶界面層 (Frontend)                        │
│  HTML/CSS/JS - 響應式 Web 應用 (http://localhost:5000)         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API 層 (Backend)                            │
│  Flask 框架 - REST API 端點                                      │
│  - /api/plan/generate - 行程規劃                               │
│  - /api/search - 數據搜尋                                       │
│  - /api/destination - 目的地信息                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
    ┌──────────────┐ ┌──────────┐ ┌──────────────┐
    │  數據處理層  │ │ AI 層    │ │  RAG 層      │
    │ (Processor)  │ │(Ollama)  │ │(檢索引擎)    │
    └──────────────┘ └──────────┘ └──────────────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
    ┌──────────────┐ ┌──────────┐ ┌──────────────┐
    │  爬蟲層      │ │數據存儲  │ │向量數據庫    │
    │ (Scrapers)   │ │(JSON/CSV)│ │(向量索引)    │
    └──────────────┘ └──────────┘ └──────────────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
    ┌──────────────────┐     ┌──────────────────┐
    │  TDX API         │     │  旅遊網站        │
    │ (交通部開放數據)  │     │ (KKday/Klook等)  │
    └──────────────────┘     └──────────────────┘
```

## 核心模塊說明

### 1. 爬蟲層 (Scraper Layer)

**文件：** `backend/scraper.py`, `scripts/Taiwan.py`, `scripts/taiwan1.py`

**功能：**
- TDX API 爬蟲：抓取官方景點、餐廳、飯店數據
- 旅遊網站爬蟲：抓取 KKday、Klook 等旅遊套餐
- 數據清理和標準化

**主要類：**
```python
class TDXScraper:
    - fetch_scenic_spots()  # 景點
    - fetch_restaurants()   # 餐廳
    - fetch_hotels()       # 飯店

class DataProcessor:
    - save_json()          # 保存 JSON
    - save_csv()           # 保存 CSV
    - merge_data()         # 合併數據
    - deduplicate()        # 去重
```

**輸出格式：**
```json
{
    "type": "景點",
    "名稱": "台北101",
    "縣市": "台北",
    "區域": "信義區",
    "描述": "...",
    "地址": "...",
    "經度": 121.5,
    "緯度": 25.0,
    "來源": "TDX"
}
```

### 2. AI 層 (AI Integration Layer)

**文件：** `backend/ollama_integration.py`

**功能：**
- Ollama 客戶端管理
- LLM 推理
- RAG 系統
- 旅遊規劃

**主要類：**
```python
class OllamaClient:
    - list_models()        # 列出模型
    - generate_response()  # 生成回應
    - chat()              # 對話

class RAGSystem:
    - load_knowledge_base()     # 載入知識庫
    - retrieve_relevant_info()  # 檢索相關信息
    - generate_with_rag()       # 生成 + 檢索

class TourismPlanner:
    - plan_itinerary()     # 規劃行程
    - get_destination_info() # 目的地信息
```

**工作流：**
```
用戶提示
   │
   ▼
檢索相關數據 (RAG)
   │
   ▼
構建上下文
   │
   ▼
調用 Ollama 模型
   │
   ▼
生成回應
   │
   ▼
返回結果
```

### 3. API 層 (Backend API)

**文件：** `backend/app.py`

**框架：** Flask + Flask-CORS

**主要端點：**

| 方法 | 路徑 | 功能 |
|------|------|------|
| GET | `/` | 主頁 |
| GET | `/api/health` | 健康檢查 |
| GET | `/api/data/summary` | 數據統計 |
| GET | `/api/search` | 搜尋 |
| GET | `/api/locations` | 位置列表 |
| POST | `/api/plan/generate` | 生成行程 |
| GET | `/api/destination/<name>` | 目的地信息 |
| POST | `/api/scrape/tdx` | 執行爬蟲 |

**請求/響應範例：**

```bash
# 請求
curl -X POST http://localhost:5000/api/plan/generate \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "台北",
    "days": 3,
    "budget": 10000,
    "interests": ["文化", "美食"]
  }'

# 響應
{
  "status": "success",
  "itinerary": {
    "destination": "台北",
    "days": 3,
    "budget": 10000,
    "plan": "詳細行程...",
    "recommended_places": [...]
  }
}
```

### 4. 前端層 (UI Layer)

**文件：** `frontend/templates/index.html`, `frontend/static/style.css`, `frontend/static/script.js`

**技術棧：**
- HTML5 - 語義化標記
- CSS3 - 現代設計，響應式
- JavaScript ES6+ - 交互和 API 調用

**主要功能：**
- 表單輸入（目的地、天數、預算、興趣）
- 實時搜尋
- 行程展示
- 數據導出

## 數據流程

### 1. 數據收集流程

```
起始
 │
 ├─► TDX API (官方)
 │    ├─► 景點 (Attraction)
 │    ├─► 餐廳 (Restaurant)
 │    └─► 飯店 (Hotel)
 │
 ├─► KKday 爬蟲
 │    └─► 旅遊套餐
 │
 └─► Klook 爬蟲 (待實現)
      └─► 旅遊套餐

     │
     ▼
 
 數據清理/標準化
 │
 ├─► 欄位映射
 ├─► 去重處理
 ├─► 格式轉換
 └─► 驗證檢查

     │
     ▼

 存儲
 │
 ├─► JSON (完整數據)
 ├─► CSV (便於分析)
 └─► 向量庫 (RAG)
```

### 2. 行程規劃流程

```
用戶輸入
(目的地、天數、預算、興趣)
     │
     ▼
表單驗證
     │
     ▼
構建提示詞 (Prompt)
     │
     ▼
RAG 檢索相關數據
     │
     ▼
組合上下文 + 提示
     │
     ▼
調用 Ollama LLM
     │
     ▼
流式生成行程
     │
     ▼
前端展示結果
     │
     ├─► 行程摘要
     ├─► 推薦景點
     ├─► 預算分析
     └─► 導出選項
```

## 配置系統

**配置文件：** `backend/config.py`

```python
# TDX 設置
TDX_CONFIG = {
    "base_url": "https://tdx.transportdata.tw/api/tourism",
    "endpoints": {...},
    "top_limit": 500  # 觀光 OAS V2 單次最多 500 筆
}

# Ollama 設置
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "model": "qwen3:4b",
    "temperature": 0.7,    # 創意程度
    "top_k": 40,          # 候選詞數量
    "top_p": 0.9          # 累積概率
}

# RAG 設置
RAG_CONFIG = {
    "chunk_size": 500,
    "chunk_overlap": 100,
    "similarity_threshold": 0.7
}
```

## 模型選擇指南

| 模型 | 大小 | 速度 | 中文 | 用途 | 推薦 |
|------|------|------|------|------|------|
| llama2 | 4GB | ⭐⭐⭐ | ⭐⭐ | 通用 | ✓ |
| mistral | 3.8GB | ⭐⭐⭐⭐ | ⭐⭐ | 快速 | ✓ |
| neural-chat | 3.8GB | ⭐⭐⭐ | ⭐⭐⭐ | 對話 | ✓ |
| qwen | 3.8GB | ⭐⭐⭐ | ⭐⭐⭐⭐ | 中文 | ✓ |
| dolphin-mixtral | 26GB | ⭐⭐ | ⭐⭐⭐ | 強大 | 高配 |

## 擴展可能性

### 1. 數據來源
- [ ] 更多旅遊網站爬蟲
- [ ] 旅遊評論 API 集成
- [ ] 天氣數據 API
- [ ] 交通運輸 API

### 2. AI 功能
- [ ] 多語言支持
- [ ] 圖像識別（景點識別）
- [ ] 語音交互
- [ ] 個性化推薦

### 3. 用戶功能
- [ ] 用戶帳戶系統
- [ ] 行程保存和歷史
- [ ] 社群分享
- [ ] 實時協作

### 4. 商業化
- [ ] 票卷預訂整合
- [ ] 飯店預訂
- [ ] 餐廳預訂
- [ ] 導遊預約

## 性能指標

### 目標指標
- 行程生成時間：< 10 秒
- 搜尋響應時間：< 1 秒
- 系統可用性：> 99%
- 數據準確度：> 95%

### 當前性能（測試環境）
- 行程生成：15-30 秒（取決於模型）
- 搜尋：200-500ms
- API 吞吐量：10+ req/sec
- 內存使用：2-4GB

## 安全考慮

### 實現的安全措施
✅ 本地數據處理（無第三方數據外洩）  
✅ 輸入驗證和清理  
✅ 錯誤處理  
✅ 日誌記錄  

### 生產環境建議
🔒 添加 HTTPS  
🔒 實現身份驗證  
🔒 API 速率限制  
🔒 數據加密  
🔒 監控和告警  

## 部署選項

### 本地開發
```bash
python -m backend.app
```

### Docker 部署
```bash
docker build -f docker/Dockerfile -t taiwan-tourism .
docker run -p 5000:5000 taiwan-tourism
```

### 雲端部署（Heroku/AWS/GCP）
- 配置環境變量
- 設置 GPU 加速
- 配置數據庫
- 設置 CDN

## 故障恢復

### 常見問題和解決方案

| 問題 | 原因 | 解決方案 |
|------|------|---------|
| Ollama 連接失敗 | 服務未啟動 | `ollama serve` |
| 沒有模型 | 模型未下載 | `ollama pull <model>` |
| 內存不足 | 模型太大 | 使用輕量模型 |
| 行程質量差 | 數據不足 | 執行爬蟲 |
| API 返回 502 | 後端崩潰 | 查看日誌 |

## 參考資源

- [Ollama 文檔](https://ollama.ai)
- [Flask 文檔](https://flask.palletsprojects.com/)
- [TDX API](https://tdx.transportdata.tw/)
- [RAG 概念](https://arxiv.org/abs/2005.11401)

---

**最後更新：** 2026 年 5 月 7 日
