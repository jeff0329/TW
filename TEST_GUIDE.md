# Taiwan Tourism AI 系統 - 測試指南

## 測試情景 1：本地 Ollama（推薦先用這個測試）

### 步驟：

1. **安裝 Ollama**
   ```bash
   # 從 https://ollama.ai 下載並安裝
   ```

2. **下載模型**
   ```bash
   ollama pull llama2
   # 或其他模型: mistral, neural-chat 等
   ```

3. **啟動 Ollama 服務**
   ```bash
   ollama serve
   # 應該看到: listening on 127.0.0.1:11434
   ```

4. **測試連接（新開終端）**
   ```bash
   cd c:\Users\Muyu\Downloads\jeff\Taiwan
   python tests/test_ollama_connection.py
   ```

5. **選擇本地 URL**
   ```
   Enter Ollama URL (default: http://localhost:11434): 
   [按 Enter 使用默認]
   ```

---

## 測試情景 2：遠程 Ollama（別人那邊建置）

### 前置條件：
- 知道別人的 Ollama 服務器 IP 或域名
- 確認網絡連接暢通

### 步驟：

1. **測試連接**
   ```bash
   python tests/test_ollama_connection.py
   ```

2. **輸入遠程地址**
   ```
   Enter Ollama URL (default: http://localhost:11434): 
   http://別人的IP:11434
   
   例如: http://192.168.1.100:11434
   或    http://ollama.example.com:11434
   ```

3. **選擇模型進行測試**

---

## 測試情景 3：快速測試爬蟲功能（不需要 Ollama）

### 目的：
測試旅遊數據爬蟲，不依賴 AI 模型

### 步驟：

1. **只爬取數據**
   ```bash
   python -m backend.scraper
   ```

2. **查看爬取結果**
   ```bash
   ls data/  # 查看生成的 JSON 和 CSV 文件
   ```

---

## 快速測試完整系統

### 場景：本地 Ollama + 旅遊爬蟲

1. **終端 1：啟動 Ollama**
   ```bash
   ollama serve
   ```

2. **終端 2：測試連接**
   ```bash
   cd c:\Users\Muyu\Downloads\jeff\Taiwan
   python tests/test_ollama_connection.py
   ```

3. **終端 3：爬取數據（可選）**
   ```bash
   python -m backend.scraper
   ```

4. **終端 2：啟動完整系統**
   ```bash
   python scripts/start.py
   # 選擇 y 爬取數據
   # 系統會啟動 Flask 服務器
   ```

5. **訪問 Web 界面**
   ```
   打開瀏覽器: http://localhost:5000
   ```

---

## 遠程 Ollama 配置說明

### 修改 config.py（如果需要）

```python
# config.py - 第 76-84 行

OLLAMA_CONFIG = {
    "base_url": "http://別人的IP:11434",  # 改這裡
    "model": "llama2",
    "temperature": 0.7,
    "top_k": 40,
    "top_p": 0.9
}
```

### 示例配置：

**本地 Ollama：**
```python
"base_url": "http://localhost:11434"
```

**遠程 Ollama（IP 地址）：**
```python
"base_url": "http://192.168.1.100:11434"
```

**遠程 Ollama（域名）：**
```python
"base_url": "http://ai-server.company.com:11434"
```

---

## 常見問題排查

### 連接被拒絕
```
Error: Connection refused
```
**解決方案：**
- 確認 Ollama 正在運行
- 檢查防火牆設置
- 驗證 URL 和端口

### 沒有可用模型
```
Error: No models available!
```
**解決方案：**
```bash
ollama pull llama2
```

### 遠程連接超時
```
Error: Connection timeout
```
**解決方案：**
- 檢查網絡連接
- 檢查 Ollama 服務器是否正在運行
- 檢查防火牆是否允許 11434 端口

### 模型在別人那邊
**說明：** config.py 的 `model` 字段要填別人那邊有的模型名稱

查看別人有什麼模型：
```bash
python tests/test_ollama_connection.py
# 會顯示可用模型列表
```

---

## 系統流程圖

```
┌─────────────────────────────┐
│   本地 AI 旅遊規劃系統      │
├─────────────────────────────┤
│ 
│ ┌─────────────────────────┐
│ │  旅遊數據爬蟲           │
│ │  (scraper.py)           │
│ │  ├─ TDX API             │
│ │  ├─ KKday              │
│ │  └─ 其他網站           │
│ └──────────┬──────────────┘
│            │
│            ▼
│ ┌─────────────────────────┐
│ │  本地或遠程 Ollama      │
│ │  ├─ 本地: localhost     │
│ │  └─ 遠程: 別人的IP      │
│ └──────────┬──────────────┘
│            │
│            ▼
│ ┌─────────────────────────┐
│ │  AI 行程規劃引擎        │
│ │  (backend/ollama_integration.py)│
│ │  ├─ RAG 檢索           │
│ │  ├─ LLM 生成           │
│ │  └─ 結果格式化         │
│ └──────────┬──────────────┘
│            │
│            ▼
│ ┌─────────────────────────┐
│ │  Flask REST API         │
│ │  (app.py)               │
│ └──────────┬──────────────┘
│            │
│            ▼
│ ┌─────────────────────────┐
│ │  Web 界面               │
│ │  (HTML/CSS/JavaScript)  │
│ │  http://localhost:5000  │
│ └─────────────────────────┘
│
└─────────────────────────────┘
```

---

## 建議的測試流程

### 第 1 階段：驗證環境
```bash
# 檢查 Python 依賴
python -c "import flask, requests, ollama; print('OK')"

# 測試爬蟲
python -m backend.scraper
```

### 第 2 階段：測試 Ollama 連接
```bash
python tests/test_ollama_connection.py
```

### 第 3 階段：完整系統測試
```bash
python scripts/start.py
# 或指定爬取數據
python scripts/start.py --scrape
```

### 第 4 階段：Web 界面測試
- 訪問 http://localhost:5000
- 測試旅遊規劃功能

---

## 聯絡支持

如有問題，檢查以下文件：
- `logs/scraper.log` - 爬蟲日誌
- `logs/` - 系統運行日誌
- `data/` - 爬取的數據

