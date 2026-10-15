import re
from urllib.parse import urlparse
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter

# Search Intent Keywords & Indicators
INTENT_INDICATORS = {
    'Informational': [
        'how to', 'guide', 'tutorial', 'what is', 'tips', 'best practices',
        'complete guide', 'explained', 'overview', 'definition', 'learn',
        'ideas', 'checklist', 'strategies', 'examples', 'history of', 'method'
    ],
    'Commercial': [
        'best', 'top', 'vs', 'versus', 'review', 'reviews', 'comparison',
        'compare', 'rated', 'affordable', 'alternative', 'alternatives',
        'pros and cons', 'recommended', 'buyers guide'
    ],
    'Transactional': [
        'buy', 'order', 'pricing', 'price', 'purchase', 'discount', 'coupon',
        'shop', 'deal', 'deals', 'sale', 'cart', 'checkout', 'subscribe',
        'quote', 'hire', 'estimate', 'cost', 'costs'
    ],
    'Navigational_Local': [
        'login', 'sign in', 'contact', 'about us', 'support', 'near me',
        'in denver', 'in boulder', 'in chicago', 'in new york', 'services in',
        'headquarters', 'locations', 'directions'
    ]
}

# Stopwords to filter out during topic extraction
STOPWORDS: Set[str] = {
    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'more',
    'your', 'will', 'are', 'was', 'were', 'our', 'all', 'can', 'has',
    'been', 'any', 'one', 'they', 'what', 'when', 'where', 'how', 'who',
    'page', 'home', 'site', 'website', 'online', 'com', 'http', 'https',
    'about', 'contact', 'copyright', 'reserved', 'rights'
}

def clean_slug_tokens(url: str) -> List[str]:
    """Extracts semantic word tokens from a URL path."""
    parsed = urlparse(url)
    path = parsed.path.lower().strip('/')
    # Split on slashes, dashes, underscores, and dots
    tokens = re.split(r'[/_\-.]+', path)
    return [t for t in tokens if len(t) > 2 and t not in STOPWORDS and not t.isdigit()]

def calculate_slug_similarity(url1: str, url2: str) -> float:
    """
    Computes Jaccard similarity between URL path/slug word tokens.
    Returns 0.0 to 100.0%.
    """
    toks1 = set(clean_slug_tokens(url1))
    toks2 = set(clean_slug_tokens(url2))
    if not toks1 or not toks2:
        return 0.0
    intersection = len(toks1.intersection(toks2))
    union = len(toks1.union(toks2))
    if union == 0:
        return 0.0
    return round((intersection / union) * 100.0, 1)

def detect_search_intent(title: str, h1_list: List[str], main_text: str, url: str) -> Tuple[str, float]:
    """
    Classifies the primary search intent of a page:
    - Informational: Research, learning, comprehensive guides
    - Commercial: Comparing options, 'best', reviews, evaluation
    - Transactional: Purchasing, pricing, hiring, quotes
    - Navigational/Local: Local landing page, specific service location, contact/about
    """
    combined_header = f"{title} {' '.join(h1_list)} {url}".lower()
    combined_body = main_text[:2000].lower() if main_text else ""

    scores: Dict[str, float] = {
        'Informational': 0.0,
        'Commercial': 0.0,
        'Transactional': 0.0,
        'Navigational_Local': 0.0
    }

    # Weight title and H1 heavily (x3)
    for intent, patterns in INTENT_INDICATORS.items():
        for pat in patterns:
            if re.search(r'\b' + re.escape(pat) + r'\b', combined_header):
                scores[intent] += 3.0
            if re.search(r'\b' + re.escape(pat) + r'\b', combined_body):
                scores[intent] += 1.0

    # Default to Informational if no strong transactional/commercial signals
    best_intent = 'Informational'
    max_score = 0.0
    for intent, score in scores.items():
        if score > max_score:
            max_score = score
            best_intent = intent

    # Map Navigational_Local to readable name
    readable_intent = "Navigational / Local" if best_intent == 'Navigational_Local' else best_intent
    confidence = min(95.0, round(50.0 + (max_score * 8.0), 1)) if max_score > 0 else 55.0

    return readable_intent, confidence

def extract_primary_topic(title: str, h1_list: List[str], main_text: str) -> str:
    """
    Extracts the dominant 2-3 word topical theme of the page from headings and title.
    """
    headline_text = f"{title} {' '.join(h1_list)}".lower()
    words = re.findall(r'\b[a-z]{3,}\b', headline_text)
    filtered = [w for w in words if w not in STOPWORDS]

    if len(filtered) >= 2:
        # Form 2-grams
        bigrams = [f"{filtered[i]} {filtered[i+1]}" for i in range(len(filtered) - 1)]
        counts = Counter(bigrams)
        if counts:
            most_common = counts.most_common(1)[0][0]
            return most_common.title()

    if filtered:
        return " ".join(filtered[:3]).title()

    # Fallback to first few words of main text
    body_words = [w for w in re.findall(r'\b[a-z]{3,}\b', main_text.lower()) if w not in STOPWORDS]
    if len(body_words) >= 2:
        return f"{body_words[0]} {body_words[1]}".title()

    return "General Topic"

def match_page_to_user_topics(page: Dict, user_topics: List[str]) -> Tuple[Optional[str], float]:
    """
    Evaluates a page against a user-provided list of topics.
    Matches against Title, H1, H2s, URL Slug, and Body text.
    Returns (best_matching_topic, confidence_score) or (None, 0.0).
    """
    if not user_topics:
        return None, 0.0

    title = page.get('title', '').lower()
    h1 = " ".join(page.get('h1', [])).lower()
    h2 = " ".join(page.get('h2', [])).lower()
    slug_tokens = set(clean_slug_tokens(page.get('original_url', '')))
    body = page.get('main_text', '')[:3000].lower()

    best_topic = None
    best_score = 0.0

    for raw_topic in user_topics:
        topic_clean = raw_topic.strip()
        if not topic_clean:
            continue

        topic_lower = topic_clean.lower()
        topic_words = [w for w in re.findall(r'\b[a-z]{3,}\b', topic_lower) if w not in STOPWORDS]
        if not topic_words:
            # Topic might be short words like "SEO"
            topic_words = [w for w in re.findall(r'\b[a-z0-9]+\b', topic_lower)]
        if not topic_words:
            continue

        score = 0.0

        # Exact phrase bonus in Title or H1
        if topic_lower in title:
            score += 12.0
        if topic_lower in h1:
            score += 10.0
        if topic_lower in h2:
            score += 6.0

        # Individual word matching
        for tw in topic_words:
            if tw in title:
                score += 4.0
            if tw in h1:
                score += 3.5
            if tw in h2:
                score += 2.0
            if tw in slug_tokens:
                score += 4.0
            # Body frequency
            body_count = body.count(tw)
            score += min(6.0, body_count * 0.8)

        # Normalize by topic word count to prevent long topics from artificially winning
        norm_score = score / max(1, len(topic_words))

        if norm_score > best_score:
            best_score = norm_score
            best_topic = topic_clean

    # Minimum threshold to avoid false-positive assignments
    if best_score >= 2.5:
        confidence = min(99.0, round(40.0 + (best_score * 5.0), 1))
        return best_topic, confidence

    return None, 0.0
