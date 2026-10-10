#!/usr/bin/env python3
"""
Taiwan Tourism Planning Assistant - Startup Script
Quick startup for the entire system
"""

import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import OLLAMA_CONFIG

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TourismPlatformStarter:
    """Tourism Planning Platform Starter"""
    
    def __init__(self):
        self.project_dir = PROJECT_ROOT
        self.data_dir = self.project_dir / "data"
        self.logs_dir = self.project_dir / "logs"
        
    def setup_directories(self):
        """Create necessary directories"""
        logger.info("Creating directory structure...")
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        logger.info("Directories created")
    
    def check_ollama(self):
        """Check Ollama connection"""
        logger.info("Checking Ollama connection...")
        base_url = OLLAMA_CONFIG.get("base_url", "http://localhost:11434")
        
        try:
            import requests
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                logger.info(f"Ollama connected")
                logger.info(f"   Available models: {len(models)}")
                
                if models:
                    for model in models[:3]:
                        logger.info(f"   - {model['name']}")
                    if len(models) > 3:
                        logger.info(f"   ... and {len(models) - 3} more models")
                
                return True
            else:
                logger.warning("Cannot connect to Ollama")
                return False
                
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {e}")
            logger.info("Please run: ollama serve (or start docker compose services)")
            return False
    
    def check_dependencies(self):
        """Check Python dependencies"""
        logger.info("Checking Python dependencies...")
        
        required_packages = {
            'flask': 'Flask',
            'requests': 'requests',
            'ollama': 'ollama'
        }
        
        missing = []
        for module_name, package_name in required_packages.items():
            try:
                __import__(module_name)
                logger.info(f"OK: {package_name}")
            except ImportError:
                logger.warning(f"NOT INSTALLED: {package_name}")
                missing.append(package_name)
        
        if missing:
            logger.warning(f"Missing packages: {', '.join(missing)}")
            logger.info(f"Run: pip install {' '.join(missing)}")
            return False
        
        return True
    
    def check_data(self):
        """Check tourism data"""
        logger.info("Checking tourism data...")
        
        data_files = list(self.data_dir.glob("*.json"))
        
        if data_files:
            logger.info(f"Found {len(data_files)} data files")
            for f in data_files[:3]:
                logger.info(f"   - {f.name}")
            if len(data_files) > 3:
                logger.info(f"   ... and {len(data_files) - 3} more files")
            return True
        else:
            logger.warning("No tourism data files found")
            logger.info("Please run: python -m backend.scraper")
            return False
    
    def run_scraper(self):
        """Execute scraper"""
        logger.info("\n" + "="*50)
        logger.info("Running tourism data scraper")
        logger.info("="*50)
        
        try:
            from backend.scraper import main as scraper_main
            data = scraper_main()
            logger.info(f"Scraper complete: collected {len(data)} data items")
            return True
        except Exception as e:
            logger.error(f"Scraper execution failed: {e}")
            return False
    
    def start_flask_server(self):
        """Start Flask server"""
        logger.info("\n" + "="*50)
        logger.info("Starting Flask API server")
        logger.info("="*50)
        
        try:
            from backend.app import app, initialize_app
            
            logger.info("Initializing application...")
            initialize_app()
            
            logger.info("Server started successfully")
            logger.info("Access address: http://localhost:5000")
            logger.info("Press Ctrl+C to stop server\n")
            
            app.run(
                host='0.0.0.0',
                port=5000,
                debug=False
            )
            
        except Exception as e:
            logger.error(f"Server startup failed: {e}")
            return False
    
    def run(self, scrape_data=False):
        """Main execution flow"""
        logger.info("\n" + "="*70)
        logger.info("Taiwan Tourism Planning Assistant - System Startup")
        logger.info("="*70 + "\n")
        
        # 1. Create directories
        self.setup_directories()
        
        # 2. Check dependencies
        if not self.check_dependencies():
            logger.error("Dependency check failed, please install missing packages")
            sys.exit(1)
        
        # 3. Check Ollama

        ollama_ready = self.check_ollama()
        
        if not ollama_ready:
            response = input("\nOllama not connected. Continue? (y/n): ").lower()
            if response != 'y':
                logger.info("Startup cancelled")
                sys.exit(0)
        
        # 4. Check data

        data_ready = self.check_data()
        
        if not data_ready and not scrape_data:
            response = input("\nTourism data needs to be collected. Continue? (y/n): ").lower()
            if response == 'y':
                scrape_data = True
            else:
                logger.info("Warning: No data available, system may not work properly")
        
        # 5. Execute scraper (if needed)
        if scrape_data:
            self.run_scraper()
        
        # 6. Start Flask server
        self.start_flask_server()


def main():
    """Main program entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Taiwan Tourism Planning Assistant - System Startup'
    )
    parser.add_argument(
        '--scrape',
        action='store_true',
        help='Execute data scraper'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Check system status only'
    )
    
    args = parser.parse_args()
    
    starter = TourismPlatformStarter()
    
    if args.check_only:
        logger.info("Checking system status...\n")
        starter.setup_directories()
        starter.check_dependencies()
        starter.check_ollama()
        starter.check_data()
        logger.info("\nCheck complete")
    else:
        try:
            starter.run(scrape_data=args.scrape)
        except KeyboardInterrupt:
            logger.info("\n\nSystem shutdown")
            sys.exit(0)
        except Exception as e:
            logger.error(f"\nSystem error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
