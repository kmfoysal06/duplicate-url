import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import requests
from typing import Dict, Tuple

class RobotsChecker:
    """
    Manages and caches robots.txt rules per host to ensure polite crawling.
    Respects robots.txt while avoiding crawling hangs if a domain's robots.txt is unavailable.
    """
    def __init__(self, user_agent: str = "SEODuplicateBot/1.0", timeout: int = 5):
        self.user_agent = user_agent
        self.timeout = timeout
        self.cache: Dict[str, Tuple[RobotFileParser, float]] = {}
        self.cache_ttl = 3600  # 1 hour cache

    def _get_parser(self, url: str) -> RobotFileParser:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        
        now = time.time()
        if origin in self.cache:
            parser, timestamp = self.cache[origin]
            if now - timestamp < self.cache_ttl:
                return parser

        robots_url = f"{origin}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            resp = requests.get(
                robots_url,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout,
                allow_redirects=True
            )
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
            elif resp.status_code in (401, 403):
                # If robots.txt is forbidden, standard convention is to assume disallowed
                parser.disallow_all = True
            elif resp.status_code == 404:
                # 404 means no restrictions
                parser.allow_all = True
            else:
                parser.allow_all = True
        except Exception:
            # If robots.txt cannot be fetched (e.g. timeout or DNS error), allow by default
            parser.allow_all = True

        self.cache[origin] = (parser, now)
        return parser

    def is_allowed(self, url: str) -> bool:
        """
        Returns True if the URL is allowed to be crawled according to robots.txt.
        """
        try:
            parser = self._get_parser(url)
            return parser.can_fetch(self.user_agent, url)
        except Exception:
            return True
