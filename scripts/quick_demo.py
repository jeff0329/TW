#!/usr/bin/env python3
"""
台灣旅遊 AI 系統 - 快速測試版本（無需 Ollama）
用於快速驗證網頁和功能
"""

import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """快速啟動 Flask 服務器"""
    
    logger.info("\n" + "="*70)
    logger.info("Taiwan Tourism AI System - Quick Demo Mode")
    logger.info("="*70 + "\n")
    
    # 檢查目錄
    logger.info("Setting up directories...")
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # 導入 Flask 應用
    try:
        logger.info("Loading Flask application...")
        from backend.app import app
        
        logger.info("\n" + "="*70)
        logger.info("Flask API Server Starting - Demo Mode")
        logger.info("="*70)
        logger.info("Address: http://localhost:5000")
        logger.info("Web Interface: http://localhost:5000")
        logger.info("\nNote: AI features will use mock responses")
        logger.info("Press Ctrl+C to stop server\n")
        
        # 啟動 Flask
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        logger.info("\n\nServer stopped")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
