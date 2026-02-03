import asyncio
import random
import logging
from playwright.async_api import async_playwright
from playwright_stealth import stealth
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self, headless=True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.ua = UserAgent()
        
    async def initialize(self):
        """Starts the Playwright engine."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            # Launch configs - simplified for reliability
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            logger.info("BrowserManager initialized.")

    async def get_page(self, proxy_server=None):
        """Creates a new context and page with stealth settings."""
        if not self.browser:
            await self.initialize()

        # Randomize Context
        user_agent = self.ua.random
        viewport = random.choice([
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1536, 'height': 864},
            {'width': 1440, 'height': 900},
        ])
        
        # Proxy Config
        proxy_config = None
        if proxy_server:
            proxy_config = {"server": proxy_server}

        # Randomize Permissions
        permissions_pool = ['geolocation', 'notifications', 'midi', 'camera']
        granted_permissions = random.sample(permissions_pool, k=random.randint(0, len(permissions_pool)))

        # Create Context with Advanced Fingerprinting
        context = await self.browser.new_context(
            user_agent=user_agent,
            viewport=viewport,
            proxy=proxy_config,
            locale='en-US',
            timezone_id='America/New_York', # Ideal: Match this to proxy IP location
            geolocation={'latitude': 40.7128, 'longitude': -74.0060}, # Example: NYC (Should match proxy)
            permissions=granted_permissions,
            java_script_enabled=True,
            has_touch=random.choice([True, False]),
            is_mobile=random.choice([True, False]),
            color_scheme=random.choice(['dark', 'light', 'no-preference']),
        )

        # Inject Stealth Scripts
        page = await context.new_page()
        await stealth(page)
        
        # Additional Canvas Noise Injection (Randomized)
        await page.add_init_script("""
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                if (type === 'image/png' && this.width > 50 && this.height > 50) {
                    const ctx = this.getContext('2d');
                    // Inject random, extremely subtle noise
                    const x = Math.floor(Math.random() * this.width);
                    const y = Math.floor(Math.random() * this.height);
                    const r = Math.floor(Math.random() * 255);
                    const g = Math.floor(Math.random() * 255);
                    const b = Math.floor(Math.random() * 255);
                    ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.01)`;
                    ctx.fillRect(x, y, 1, 1);
                }
                return originalToDataURL.apply(this, arguments);
            };
            
            // WebGL Noise
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                // UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                // UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, [parameter]);
            };
        """)

        return page, context

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
