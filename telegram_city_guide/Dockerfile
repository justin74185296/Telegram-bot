# Telegram City Guide Bot - Dockerfile
FROM python:3.12-slim

# 設定工作目錄
WORKDIR /app

# 複製依賴檔案
COPY requirements.txt .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 執行 Bot
CMD ["python", "main.py"]
