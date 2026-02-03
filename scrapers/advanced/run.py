import sys
import asyncio
import os

# FIXED: Must be set before any other asyncio/reactor imports on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from tennis_scraper.spiders.atp_spider import ATPSpider

def main():
    """
    Industrial-grade entry point using CrawlerProcess.
    Allows running multiple spiders or configuring the process programmatically.
    """
    # Ensure project settings are loaded
    os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'tennis_scraper.settings')
    settings = get_project_settings()

    # Override settings at runtime if needed (e.g., from Env Vars)
    # settings.set('LOG_LEVEL', 'DEBUG')

    process = CrawlerProcess(settings)
    
    # Schedule the spider
    process.crawl(ATPSpider)
    
    print("Starting Industrial Scraper Process...")
    process.start() # Blocks here until all crawlers are finished

if __name__ == '__main__':
    main()
