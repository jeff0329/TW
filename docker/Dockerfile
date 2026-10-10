FROM python:3.10-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 複製項目文件
COPY . /app/

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 建立數據目錄
RUN mkdir -p data logs

# 暴露端口
EXPOSE 5000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# 啟動應用
CMD ["python", "-m", "backend.app"]
