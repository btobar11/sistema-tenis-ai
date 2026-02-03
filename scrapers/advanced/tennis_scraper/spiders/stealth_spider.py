import scrapy
import datetime

class StealthSpider(scrapy.Spider):
    name = "stealth_check"
    allowed_domains = ["browserscan.net", "bot.sannysoft.com"]
    start_urls = ["https://bot.sannysoft.com/"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'wait_for': 'body'
                }
            )

    async def parse(self, response):
        self.logger.info(f"Checking Stealth on: {response.url}")
        
        # Capture Screenshot to prove stealth (saved to local directory)
        page = response.meta.get('playwright_page') # Access if middleware attaches it, or we rely on 'body'
        # Middleware currently doesn't attach the page object to response.meta for the spider to use directly 
        # normally, but we can dump the body to see results.
        
        # However, to be "Best Possible", we should save the HTML to inspect specifically for "WebDriver: absent"
        
        filename = f"stealth_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, 'wb') as f:
            f.write(response.body)
            
        self.logger.info(f"Saved Stealth Report to {filename}")
        
        # Simple assertions
        webdriver = response.css('td:contains("WebDriver") + td::text').get()
        self.logger.info(f"WebDriver Status detected: {webdriver}")
        
        if webdriver and "absent" in webdriver.lower():
             self.logger.info("✅ SUCCESS: WebDriver is hidden.")
        else:
             self.logger.warning(f"⚠️ ATTENTION: WebDriver status is '{webdriver}'")
