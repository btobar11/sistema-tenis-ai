import asyncio
import random
from scrapy import signals
from scrapy.http import HtmlResponse
from .browser_manager import BrowserManager
from .proxy_manager import ProxyManager

class PlaywrightMiddleware:
    def __init__(self):
        self.browser_manager = BrowserManager(headless=True)
        self.proxy_manager = ProxyManager()

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    async def spider_opened(self, spider):
        await self.browser_manager.initialize()
        spider.logger.info("Playwright Middleware: Browser initialized.")

    async def spider_closed(self, spider):
        await self.browser_manager.close()
        spider.logger.info("Playwright Middleware: Browser closed.")

    async def process_request(self, request, spider):
        # Only process requests that need rendering or specific stealth
        if not request.meta.get('playwright', False):
            return None

        page = None
        context = None
        try:
            proxy = self.proxy_manager.get_proxy()
            page, context = await self.browser_manager.get_page(proxy_server=proxy)

            spider.logger.info(f"Navigating to {request.url} with Playwright")
            
            # Navigate with Human simulation
            response = await page.goto(request.url, wait_until='domcontentloaded', timeout=60000)
            
            # Human Behavior Simulation
            await self._simulate_human_behavior(page)

            # Wait for specific selector if requested
            wait_for = request.meta.get('wait_for')
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=10000)
                except Exception:
                    spider.logger.warning(f"Timeout waiting for selector: {wait_for}")

            content = await page.content()
            
            # Construct Scrapy Response
            return HtmlResponse(
                url=page.url,
                status=response.status if response else 200,
                body=content,
                encoding='utf-8',
                request=request
            )

        except Exception as e:
            spider.logger.error(f"Playwright Error on {request.url}: {e}")
            return None # Fallback or retry logic handled by Scrapy
        finally:
            if page: await page.close()
            if context: await context.close()

    async def _simulate_human_behavior(self, page):
        """Injects random mouse movements and delays."""
        # Random Wait
        await asyncio.sleep(random.uniform(1.0, 3.5))
        
        # Random Mouse Move
        # Simple implementation - Bezier curve libraries exist but simple random steps work for basic presence
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 1200)
            y = random.randint(100, 800)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Scroll down slightly
        await page.mouse.wheel(0, random.randint(100, 500))
        await asyncio.sleep(random.uniform(0.5, 1.5))
