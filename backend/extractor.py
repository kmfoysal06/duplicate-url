import re
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup, Comment
from url_utils import resolve_url

# HTML tags that are never part of primary article content
BOILERPLATE_TAGS = [
    'script', 'style', 'noscript', 'header', 'footer', 'nav', 'aside',
    'svg', 'iframe', 'canvas', 'form', 'button', 'input', 'select', 'textarea',
    'meta', 'link'
]

# Common boilerplate classes and IDs to remove or deprioritize
BOILERPLATE_SELECTORS = [
    '.cookie-banner', '.cookie-notice', '#cookie-consent',
    '.sidebar', '#sidebar', '.newsletter-signup', '.popup',
    '.advertisement', '.ad-box', '.share-buttons', '.social-share',
    '.site-footer', '.site-header', '.site-nav', '.top-nav', '.mobile-menu'
]

def clean_text(text: str) -> str:
    """Collapses spaces and trims whitespace."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def normalize_text_for_hash(text: str) -> str:
    """Normalizes text by lowercasing, stripping punctuation, and collapsing whitespace."""
    lower = text.lower()
    cleaned = re.sub(r'[^\w\s]', '', lower)
    return re.sub(r'\s+', ' ', cleaned).strip()

def extract_page_data(html_content: str, final_url: str) -> Dict:
    """
    Parses HTML content using BeautifulSoup and extracts semantic SEO elements:
    - Page title
    - Meta description
    - H1 and H2 headings
    - Canonical URL
    - Main page text (with boilerplate removal and semantic container preference)
    - Word count
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Page Title
    title = ""
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        title = clean_text(title_tag.string)

    # 2. Meta Description
    meta_desc = ""
    meta_tag = soup.find('meta', attrs={'name': re.compile(r'^description$', re.I)}) or \
               soup.find('meta', attrs={'property': re.compile(r'^og:description$', re.I)})
    if meta_tag and meta_tag.get('content'):
        meta_desc = clean_text(meta_tag.get('content'))

    # 3. Canonical URL
    canonical_url = None
    canonical_tag = soup.find('link', attrs={'rel': re.compile(r'\bcanonical\b', re.I)})
    if canonical_tag and canonical_tag.get('href'):
        canonical_raw = canonical_tag.get('href').strip()
        canonical_url = resolve_url(final_url, canonical_raw)

    # 4. Headings (H1 and H2)
    h1_list: List[str] = []
    for h in soup.find_all('h1'):
        text = clean_text(h.get_text())
        if text:
            h1_list.append(text)

    h2_list: List[str] = []
    for h in soup.find_all('h2'):
        text = clean_text(h.get_text())
        if text and text not in h2_list:
            h2_list.append(text)

    # 5. Remove comments
    for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    # 6. Remove obvious boilerplate tags
    for tag_name in BOILERPLATE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove known boilerplate CSS selectors
    for selector in BOILERPLATE_SELECTORS:
        try:
            for el in soup.select(selector):
                el.decompose()
        except Exception:
            pass

    # 7. Semantic Main Content Extraction
    # Preference: <main>, <article>, [role="main"], #content, .content, etc.
    main_candidate = None
    semantic_candidates = soup.find_all(['main', 'article']) or \
                          soup.find_all(attrs={'role': 'main'}) or \
                          soup.find_all(id=re.compile(r'^(main-content|main|content|article|post-body)$', re.I)) or \
                          soup.find_all(class_=re.compile(r'\b(main-content|article-content|entry-content|post-content)\b', re.I))

    # Look for candidate with substantial text
    best_candidate = None
    max_words = 0
    for cand in semantic_candidates:
        cand_text = clean_text(cand.get_text())
        words = len(cand_text.split())
        if words > max_words:
            max_words = words
            best_candidate = cand

    # Fallback to body or remaining soup if semantic container has very little text
    if best_candidate and max_words >= 30:
        main_text = clean_text(best_candidate.get_text(separator=' '))
    else:
        body = soup.find('body')
        if body:
            main_text = clean_text(body.get_text(separator=' '))
        else:
            main_text = clean_text(soup.get_text(separator=' '))

    # Calculate word count
    words = [w for w in main_text.split() if w]
    word_count = len(words)

    return {
        'title': title,
        'meta_description': meta_desc,
        'canonical_url': canonical_url,
        'h1': h1_list,
        'h2': h2_list,
        'main_text': main_text,
        'word_count': word_count
    }
