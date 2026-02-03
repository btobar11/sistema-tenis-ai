BOT_NAME = 'tennis_scraper'

SPIDER_MODULES = ['tennis_scraper.spiders']
NEWSPIDER_MODULE = 'tennis_scraper.spiders'

# Obey robots.txt rules (We are "polite" technically, but we are evading detection so often we disable this)
ROBOTSTXT_OBEY = False

# Concurrency
CONCURRENT_REQUESTS = 4
DOWNLOAD_DELAY = 2

# Cookies
COOKIES_ENABLED = True

# Middleware
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 500,
    'tennis_scraper.middlewares.PlaywrightMiddleware': 543,
}

# Pipelines
ITEM_PIPELINES = {
   'tennis_scraper.pipelines.SupabasePipeline': 300,
}

# Retry Policy (Exponential Backoff)
RETRY_ENABLED = True
RETRY_TIMES = 5  # High retry count for rotation
RETRY_HTTP_CODES = [403, 429, 500, 502, 503, 504]
RETRY_PRIORITY_ADJUST = -1

# Randomize Download Delay (0.5 * DOWNLOAD_DELAY to 1.5 * DOWNLOAD_DELAY)
RANDOMIZE_DOWNLOAD_DELAY = True


# Twisted Reactor
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Logging
LOG_LEVEL = 'INFO'
