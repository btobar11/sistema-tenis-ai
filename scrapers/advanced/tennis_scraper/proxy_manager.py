import random
import os
import logging

logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self, proxy_list=None):
        self.proxies = proxy_list or self._load_proxies()
        self.current_index = 0

    def _load_proxies(self):
        """
        Load proxies from env or file.
        Format: http://user:pass@host:port
        """
        proxies = []
        # 1. Check ENV
        env_proxy = os.getenv("ROTATING_PROXY_URL")
        if env_proxy:
            proxies.append(env_proxy)
            
        # 2. Check File (optional)
        # if os.path.exists("proxies.txt"): ...
        
        if not proxies:
            logger.warning("No proxies configured. Using direct connection (Risk of ban).")
            return []
            
        return proxies

    def get_proxy(self):
        """Returns a proxy to use. Implements simple rotation."""
        if not self.proxies:
            return None
            
        # Random or Round Robin
        # For 'sticky' sessions, maybe keep same one. For scraping, random often better.
        return random.choice(self.proxies)

    def report_ban(self, proxy):
        """Handle logic for when a proxy is banned (remove from pool)."""
        logger.warning(f"Proxy reported banned: {proxy}")
        # In a sophisticated system, we'd temporarily disable it.
