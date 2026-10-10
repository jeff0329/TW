"""
Taiwan Tourism Data Scraper - Main Program
Integrate TDX API data collection
"""

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.scraper import TDXScraper, DataProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_data_for_ollama_ultra():
    """Fetch and store Taiwan tourism data"""
    
    logger.info("Starting Taiwan tourism data scraper...")
    logger.info("="*50)
    
    # Initialize scraper and data processor
    scraper = TDXScraper()
    processor = DataProcessor()
    project_dir = PROJECT_ROOT
    
    # Ensure data directory exists
    (project_dir / "data").mkdir(exist_ok=True)
    
    try:
        # 1. Fetch scenic spots
        logger.info("\nFetching scenic spot data...")
        scenic_spots = scraper.fetch_scenic_spots()
        
        # 2. Fetch restaurants
        logger.info("\nFetching restaurant data...")
        restaurants = scraper.fetch_restaurants()
        
        # 3. Fetch hotels
        logger.info("\nFetching hotel data...")
        hotels = scraper.fetch_hotels()
        
        # 4. Merge all data
        logger.info("\nMerging data...")
        all_data = scenic_spots + restaurants + hotels
        
        # 5. Deduplicate
        logger.info("\nPerforming deduplication...")
        unique_data = processor.deduplicate(all_data)
        
        # 6. Save data
        logger.info("\nSaving data...")
        processor.save_json(unique_data, "taiwan_tourism_db.json")
        processor.save_csv(unique_data, "taiwan_tourism_db.csv")
        
        # 7. Save by category
        if scenic_spots:
            processor.save_json(scenic_spots, "scenic_spots.json")
            processor.save_csv(scenic_spots, "scenic_spots.csv")
        
        if restaurants:
            processor.save_json(restaurants, "restaurants.json")
            processor.save_csv(restaurants, "restaurants.csv")
        
        if hotels:
            processor.save_json(hotels, "hotels.json")
            processor.save_csv(hotels, "hotels.csv")
        
        logger.info("\n" + "="*50)
        logger.info("Scraper execution complete")
        logger.info(f"Total: {len(unique_data)} data items")
        logger.info(f"   - Scenic spots: {len(scenic_spots)}")
        logger.info(f"   - Restaurants: {len(restaurants)}")
        logger.info(f"   - Hotels: {len(hotels)}")
        logger.info("="*50)
        
        return unique_data
        
    except Exception as e:
        logger.error(f"Scraper execution failed: {e}")
        raise


if __name__ == "__main__":
    data = fetch_data_for_ollama_ultra()