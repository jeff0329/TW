# ✅ 台灣旅遊規劃助手 - 完整安裝指南

## 📋 目錄

1. [系統要求](#系統要求)
2. [前置準備](#前置準備)
3. [安裝步驟](#安裝步驟)
4. [運行應用](#運行應用)
5. [驗證安裝](#驗證安裝)
6. [常見問題](#常見問題)

---

## 系統要求

### 硬體
- **CPU**: 2 核以上
- **RAM**: 8GB 推薦（最少 4GB）
- **硬碟**: 50GB+ (用於模型和數據)
- **GPU**: 可選（NVIDIA/AMD 加速）

### 軟體
- Windows 10+ / macOS 10.14+ / Linux
- Python 3.9+
- Ollama 最新版本
- 網絡連接

---

## 前置準備

### 1️⃣ 安裝 Ollama

#### Windows/Mac
1. 訪問 [ollama.com](https://ollama.com)
2. 下載對應版本
3. 執行安裝程式

#### Linux
```bash
curl https://ollama.ai/install.sh | sh
```

### 2️⃣ 驗證 Ollama 安裝

```bash
# 檢查版本
ollama --version

# 應該看到：ollama version X.X.X
```

### 3️⃣ 確保 Python 3.9+

```bash
python --version
# 或
python3 --version

# 應該看到：Python 3.9.x 或更高
```

---

## 安裝步驟

### 步驟 1：啟動 Ollama 服務

```bash
# 在新終端打開 Ollama 服務
ollama serve
```

✅ 看到 `Listening on` 表示成功

### 步驟 2：下載 LLM 模型（在新終端）

```bash
# 推薦：llama2（平衡速度和質量）
ollama pull llama2

# 或者：mistral（更快）
ollama pull mistral

# 或者：neural-chat（對話優化）
ollama pull neural-chat
```

⏳ 首次下載需要 5-15 分鐘，模型大小 3-4GB

### 步驟 3：驗證模型下載

```bash
ollama list
```

你應該看到：
```
NAME              ID              SIZE    MODIFIED
llama2            2c05b1d6a025    3.8GB   2 minutes ago
```

### 步驟 4：進入項目目錄

```bash
cd Taiwan
```

### 步驟 5：建立虛擬環境（推薦）

```bash
# Windows
python -m venv venv
# PowerShell
.\venv\Scripts\Activate.ps1
# cmd
venv\Scripts\activate.bat

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

✅ 看到 `(venv)` 前綴表示已激活

### 步驟 6：安裝 Python 依賴

```bash
pip install -r requirements.txt
```

注意：套件版本以 [requirements.txt](requirements.txt) 為唯一準則。

⏳ 首次安裝需要 3-5 分鐘

### 步驟 7：驗證依賴安裝

```bash
python -c "import flask, requests, ollama; print('✅ 所有依賴已安裝')"
```

---

## 運行應用

### 方法 A：使用快速啟動腳本（推薦）

```bash
python scripts/start.py
```

系統會自動：
✅ 檢查依賴  
✅ 檢查 Ollama 連接  
✅ 檢查數據文件  
✅ 提示是否需要爬蟲  
✅ 啟動 Flask 服務器  

### 方法 B：直接運行爬蟲 + 服務器

```bash
# 首次運行：收集數據
python -m backend.scraper

# 啟動服務器
python -m backend.app
```

### 方法 C：手動執行各步驟

```bash
# 執行 TDX 爬蟲
python scripts/Taiwan.py

# 執行 KKday 爬蟲（需要 Playwright）
python scripts/taiwan1.py

# 若首次使用 Playwright，先安裝瀏覽器
python -m playwright install chromium

# 啟動 API 服務器
python -m backend.app
```

---

## 驗證安裝

### 1️⃣ 檢查服務器是否運行

打開新終端，執行：

```bash
curl http://localhost:5000/api/health
```

應該看到：
```json
{
  "status": "ok",
  "timestamp": "2026-05-07T...",
  "data_loaded": true,
  "planner_ready": true
}
```

### 2️⃣ 訪問 Web 界面

打開瀏覽器，訪問：
```
http://localhost:5000
```

✅ 應該看到旅遊規劃表單

### 3️⃣ 測試搜尋功能

在搜尋框輸入「台北」，應該能看到景點結果

### 4️⃣ 測試行程生成

填寫表單：
- 目的地：台北
- 天數：3
- 預算：10000
- 興趣：選擇文化、美食

點擊「生成行程」，應該在 10-30 秒內得到結果

---

## 常見問題

### ❌ Ollama 無法連接

**錯誤信息：** `Cannot connect to http://localhost:11434`

**解決方案：**
```bash
# 1. 確保 Ollama 已啟動
ollama serve

# 2. 檢查 Ollama 服務
curl http://localhost:11434/api/tags

# 3. 檢查防火牆設置
```

### ❌ 沒有可用模型

**錯誤信息：** `No models found` 或 `Model not found`

**解決方案：**
```bash
# 1. 列出已安裝的模型
ollama list

# 2. 下載模型
ollama pull llama2

# 3. 驗證下載
ollama show llama2
```

### ❌ 內存不足

**錯誤信息：** `Cannot allocate memory` 或進程被 killed

**解決方案：**
1. 切換到更輕量的模型（mistral）
2. 增加系統 RAM
3. 關閉其他應用程式

### ❌ Python 依賴缺失

**錯誤信息：** `ModuleNotFoundError: No module named 'xxx'`

**解決方案：**
```bash
# 重新安裝依賴
pip install --force-reinstall -r requirements.txt

# 檢查是否有版本衝突
pip check
```

### ❌ 沒有旅遊數據

**錯誤信息：** `No tourism data available` 或搜尋結果為空

**解決方案：**
```bash
# 執行爬蟲
python -m backend.scraper

# 或通過 API 手動觸發
curl -X POST http://localhost:5000/api/scrape/tdx
```

### ❌ 端口 5000 已被佔用

**錯誤信息：** `Address already in use`

**解決方案：**
```bash
# Windows：查找佔用 5000 端口的進程
netstat -ano | findstr :5000

# Mac/Linux：
lsof -i :5000

# 修改配置文件 app.py
app.run(port=5001)  # 改為其他端口
```

### ❌ 行程生成很慢

**原因：** 模型推理時間長

**解決方案：**
1. 使用更快的模型（mistral）
2. 確保 GPU 加速已啟用
3. 增加系統 RAM
4. 減少 RAG 檢索數量

### ❌ Web 界面無法加載

**錯誤信息：** `Cannot GET /` 或 `Connection refused`

**解決方案：**
```bash
# 1. 確保服務器在運行
# 2. 檢查服務器日誌
# 3. 清除瀏覽器快取（Ctrl+Shift+Delete）
# 4. 嘗試其他瀏覽器
```

### ❌ API 返回 500 錯誤

**解決方案：**
```bash
# 1. 查看服務器日誌（應該在控制台輸出）
# 2. 確保 Ollama 連接正常
# 3. 檢查系統資源
# 4. 重啟服務器
```

---

## 🔧 配置調整

### 切換 Ollama 模型

編輯 `backend/config.py`：

```python
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "model": "mistral",  # 改為你想要的模型
    "temperature": 0.7,
    "top_k": 40,
    "top_p": 0.9
}
```

### 改變 Flask 端口

編輯 `backend/app.py` 最後幾行：

```python
if __name__ == '__main__':
    initialize_app()
    app.run(
        host='0.0.0.0',
        port=8000,  # 改為你想要的端口
        debug=True
    )
```

### 調整 RAG 參數

編輯 `backend/config.py`：

```python
RAG_CONFIG = {
    "chunk_size": 500,           # 文本塊大小
    "chunk_overlap": 100,        # 塊之間的重疊
    "similarity_threshold": 0.7  # 相似度閾值
}
```

---

## 📊 監控系統

### 查看 API 統計

```bash
curl http://localhost:5000/api/data/summary
```

### 查看日誌

```bash
# 查看爬蟲日誌
tail -f logs/scraper.log

# Windows PowerShell
Get-Content logs/scraper.log -Tail 20 -Wait
```

---

## 🚀 下一步

1. ✅ 閱讀 [README.md](README.md) 了解完整功能
2. ✅ 查看 [API 文檔](README.md#-api-文檔) 開發集成
3. ✅ 探索 [架構設計](ARCHITECTURE.md) 理解系統
4. ✅ 查看 [快速開始](QUICK_START.md) 更多技巧

---

## 💡 最佳實踐

### 開發
```bash
# 使用虛擬環境
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
# Linux/macOS
source venv/bin/activate

# 保持依賴最新
pip install -r requirements.txt --upgrade

# 執行測試
python -m pytest tests/
```

### 生產
```bash
# 使用 Docker
docker build -f docker/Dockerfile -t taiwan-tourism .
docker run -p 5000:5000 taiwan-tourism

# 使用 Docker Compose（建議，包含 Ollama）
docker compose -f docker/docker-compose.ollama.yml up -d --build
docker exec -it taiwan-ollama ollama pull llama2
curl http://localhost:5000/api/health

# 或使用 Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

---

## 📞 技術支持

### 獲得幫助
1. 查看本文檔的常見問題部分
2. 查看 [README.md](README.md) 故障排查
3. 查看 [ARCHITECTURE.md](ARCHITECTURE.md) 了解原理
4. 提交 GitHub Issue

### 報告 Bug
```
在報告時包含：
- 操作系統和版本
- Python 版本
- Ollama 版本
- 錯誤信息和堆棧跟蹤
- 重現步驟
```

---

## ✨ 成功安裝

如果您到達這裡，恭喜！

系統應該現在可以：
✅ 爬蟲收集旅遊數據  
✅ 通過 Ollama 運行 AI 模型  
✅ 使用 RAG 架構生成準確的行程  
✅ 提供完整的 Web 界面  
✅ 提供 REST API 服務  

---

**現在開始您的旅遊規劃之旅吧！🗺️**

訪問 [http://localhost:5000](http://localhost:5000) 開始使用

---

**最後更新：** 2026 年 5 月 7 日  
**支持版本：** Python 3.9+, Ollama 最新版
