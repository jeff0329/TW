# 快速開始

台灣旅遊規劃助手（重整後分層版）

## 專案分層

```text
Taiwan/
├── backend/            # Flask API、爬蟲、Ollama/RAG 後端邏輯
├── frontend/           # templates + static 前端頁面
├── docker/             # Docker 設定
├── scripts/            # 啟動與工具腳本
├── tests/              # 測試腳本
├── data/               # 爬蟲輸出資料
└── logs/               # 執行日誌
```

## 1) 安裝依賴

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

## 2) 啟動 Ollama

```bash
ollama serve
# 首次建議拉一個模型
ollama pull llama2
```

## 3) 先抓資料（首次建議）

```bash
python -m backend.scraper
```

## 4) 啟動系統

```bash
# 完整啟動流程（會檢查依賴/Ollama/資料）
python scripts/start.py

# 只啟 API
python -m backend.app
```

開啟 http://localhost:5000

## 5) Docker（可選）

```bash
docker build -f docker/Dockerfile -t taiwan-tourism .
docker run -p 5000:5000 taiwan-tourism
```

## 常用命令

```bash
# 快速 Demo
python scripts/quick_demo.py

# TDX 資料抓取腳本
python scripts/Taiwan.py

# KKday 抓取腳本
python scripts/taiwan1.py

# 測試 Ollama 連線
python tests/test_ollama_connection.py
```
