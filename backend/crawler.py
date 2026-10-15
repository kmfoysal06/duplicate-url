import time
import requests
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable
from url_utils import is_safe_url, normalize_url
from robots_utils import RobotsChecker
from extractor import extract_page_data, normalize_text_for_hash

# Default parameters
DEFAULT_TIMEOUT = 10
DEFAULT_MAX_REDIRECTS = 5
DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB max response
DEFAULT_MAX_WORKERS = 4
DEFAULT_USER_AGENT = "SEODuplicateBot/1.0 (+https://example.com/bot; SEO Duplicate-Page Detection System)"

class SafeRedirectSession(requests.Session):
    """
    Custom session that validates SSRF safety at each redirect hop before following.
    """
    def __init__(self, allow_local_for_testing: bool = False):
        super().__init__()
        self.allow_local_for_testing = allow_local_for_testing

    def rebuild_auth(self, prepared_request, response):
        super().rebuild_auth(prepared_request, response)
        # Check SSRF on redirect target
        target_url = prepared_request.url
        safe, reason = is_safe_url(target_url, allow_local_for_testing=self.allow_local_for_testing)
        if not safe:
            raise requests.exceptions.RequestException(f"Redirect blocked by SSRF protection: {reason}")

class WebCrawler:
    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        max_workers: int = DEFAULT_MAX_WORKERS,
        max_bytes: int = DEFAULT_MAX_BYTES,
        respect_robots: bool = True,
        allow_local_for_testing: bool = False,
        user_agent: str = DEFAULT_USER_AGENT
    ):
        self.timeout = timeout
        self.max_workers = max_workers
        self.max_bytes = max_bytes
        self.respect_robots = respect_robots
        self.allow_local_for_testing = allow_local_for_testing
        self.user_agent = user_agent
        self.robots_checker = RobotsChecker(user_agent=self.user_agent, timeout=5) if respect_robots else None

    def crawl_single_page(self, url: str) -> Dict:
        """
        Crawls a single URL with SSRF protection, size limits, robots.txt check, and retries.
        """
        result = {
            'original_url': url,
            'final_url': url,
            'status_code': None,
            'title': '',
            'meta_description': '',
            'canonical_url': None,
            'h1': [],
            'h2': [],
            'main_text': '',
            'word_count': 0,
            'content_hash': None,
            'error': None
        }

        # 1. SSRF Safety Check
        safe, reason = is_safe_url(url, allow_local_for_testing=self.allow_local_for_testing)
        if not safe:
            result['error'] = f"Security: {reason}"
            return result

        # 2. Check Robots.txt if enabled
        if self.respect_robots and self.robots_checker:
            try:
                if not self.robots_checker.is_allowed(url):
                    result['error'] = "Crawling blocked by robots.txt restrictions."
                    result['status_code'] = 403
                    return result
            except Exception as e:
                pass  # Fall through gracefully if robots check errors

        # 3. Fetch with retries
        retries = 2
        last_error = None
        for attempt in range(retries + 1):
            session = SafeRedirectSession(allow_local_for_testing=self.allow_local_for_testing)
            session.max_redirects = DEFAULT_MAX_REDIRECTS
            try:
                headers = {
                    'User-Agent': self.user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                }

                # Stream response to enforce size limits
                with session.get(url, headers=headers, timeout=self.timeout, stream=True, allow_redirects=True) as resp:
                    result['status_code'] = resp.status_code
                    result['final_url'] = resp.url

                    if resp.status_code >= 400:
                        result['error'] = f"HTTP Error {resp.status_code}"
                        return result

                    # Verify Content-Type
                    content_type = resp.headers.get('Content-Type', '').lower()
                    if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
                        result['error'] = f"Unsupported content type: {content_type}"
                        return result

                    # Read up to max_bytes
                    content_chunks = []
                    bytes_read = 0
                    for chunk in resp.iter_content(chunk_size=8192):
                        bytes_read += len(chunk)
                        if bytes_read > self.max_bytes:
                            result['error'] = f"Page size exceeded {self.max_bytes // (1024 * 1024)}MB limit."
                            return result
                        content_chunks.append(chunk)

                    raw_bytes = b"".join(content_chunks)
                    # Detect encoding from response or fallback to utf-8
                    encoding = resp.encoding or 'utf-8'
                    try:
                        html_text = raw_bytes.decode(encoding, errors='replace')
                    except Exception:
                        html_text = raw_bytes.decode('utf-8', errors='replace')

                    # 4. Extract Page Data
                    extracted = extract_page_data(html_text, result['final_url'])
                    result.update(extracted)

                    # Compute content hash for exact duplicate detection
                    if result['main_text']:
                        norm_text = normalize_text_for_hash(result['main_text'])
                        result['content_hash'] = hashlib.sha256(norm_text.encode('utf-8')).hexdigest()
                    else:
                        result['content_hash'] = None

                    return result

            except requests.exceptions.Timeout:
                last_error = f"Request timed out after {self.timeout}s."
            except requests.exceptions.SSLError as e:
                last_error = f"SSL Certificate error: {str(e)}"
                break  # Don't retry SSL errors
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: could not connect to server."
            except Exception as e:
                last_error = f"Crawl error: {str(e)}"
            
            if attempt < retries:
                time.sleep(1.0 * (attempt + 1))

        result['error'] = last_error or "Unknown crawl failure."
        return result

    def crawl_urls(
        self,
        urls: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Dict]:
        """
        Crawls a list of URLs concurrently with polite concurrency limits.
        Calls progress_callback(completed, total, current_url) as each finishes.
        """
        results = []
        total = len(urls)
        completed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.crawl_single_page, url): url for url in urls}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    results.append(data)
                except Exception as e:
                    results.append({
                        'original_url': url,
                        'final_url': url,
                        'status_code': None,
                        'title': '',
                        'meta_description': '',
                        'canonical_url': None,
                        'h1': [],
                        'h2': [],
                        'main_text': '',
                        'word_count': 0,
                        'content_hash': None,
                        'error': f"Unhandled exception: {str(e)}"
                    })
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, url)

        # Restore original submission order
        order_map = {u: i for i, u in enumerate(urls)}
        results.sort(key=lambda r: order_map.get(r['original_url'], 999999))
        return results
