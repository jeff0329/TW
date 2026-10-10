"""
KKday Tourism Data Scraper
Use Playwright to scrape KKday tourism package information
"""

import json
import csv
import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_kkday_csv():
    """Fetch tourism data from KKday"""
    project_dir = Path(__file__).resolve().parent.parent
    
    url = "https://www.kkday.com/zh-tw/search?keyword=台北"
    
    logger.info("Starting KKday data scraping...")
    logger.info(f"URL: {url}")
    
    items = []
    
    try:
        with sync_playwright() as p:
            logger.info("Starting browser...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            logger.info("Loading page...")
            page.goto(url, timeout=60000)
            page.wait_for_timeout(8000)  # Wait for JS to load
            
            logger.info("Searching for elements...")
            cards = page.query_selector_all("a")
            
            logger.info(f"Found {len(cards)} links, starting extraction...")
            
            for i, c in enumerate(cards):
                try:
                    title = c.inner_text().strip()
                    link = c.get_attribute("href")
                    
                    if title and link and "kkday.com" in link:
                        item = {
                            "type": "Tourism Package",
                            "title": title,
                            "link": link,
                            "source": "KKday",
                            "scrape_date": datetime.now().isoformat()
                        }
                        items.append(item)
                        
                        if (i + 1) % 10 == 0:
                            logger.info(f"   Extracted: {len(items)} items...")
                
                except Exception as e:
                    logger.debug(f"Extraction failed: {e}")
            
            browser.close()
            logger.info("Browser closed")
        
        # Deduplicate
        logger.info("\nPerforming deduplication...")
        seen = set()
        clean = []
        
        for i in items:
            if i["link"] not in seen:
                clean.append(i)
                seen.add(i["link"])
        
        logger.info(f"Deduplication complete: {len(items)} -> {len(clean)} items")
        
        # Save data directory
        (project_dir / "data").mkdir(exist_ok=True)
        
        # JSON format
        json_filename = str(project_dir / "data" / "kkday.json")
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(clean, f, ensure_ascii=False, indent=4)
        logger.info(f"JSON: {json_filename}")
        
        # CSV format
        csv_filename = str(project_dir / "data" / "kkday.csv")
        with open(csv_filename, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["type", "title", "link", "source", "scrape_date"])
            writer.writeheader()
            writer.writerows(clean)
        logger.info(f"CSV: {csv_filename}")
        
        logger.info("\n" + "="*50)
        logger.info(f"Complete! Total {len(clean)} items")
        logger.info("="*50)
        
        return clean
    
    except Exception as e:
        logger.error(f"Scraper execution failed: {e}")
        raise


if __name__ == "__main__":
    try:
        data = fetch_kkday_csv()
    except KeyboardInterrupt:
        logger.info("\nUser cancelled")
    except Exception as e:
        logger.error(f"Error occurred: {e}")