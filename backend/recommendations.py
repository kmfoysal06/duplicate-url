from urllib.parse import urlparse
from typing import Dict, List

def generate_pair_recommendation(pair: Dict) -> str:
    """
    Generates tailored, evidence-based SEO recommendations for a pair of pages.
    Considers similarity score, canonical configuration, query parameters,
    content length, and headings.
    """
    score = pair.get('similarity_score', 0.0)
    classification = pair.get('classification', '')
    url1 = pair.get('url1', '')
    url2 = pair.get('url2', '')
    canon1 = pair.get('canonical1')
    canon2 = pair.get('canonical2')
    same_canonical = pair.get('same_canonical', False)
    words1 = pair.get('word_count1', 0)
    words2 = pair.get('word_count2', 0)
    title_match = pair.get('title_match', False)
    h1_match = pair.get('h1_match', False)
    status1 = pair.get('status_code1')
    status2 = pair.get('status_code2')

    # Check for HTTP errors or redirects
    if (status1 and status1 >= 400) or (status2 and status2 >= 400):
        return f"HTTP Status Alert: One or both URLs returned an HTTP error (Status: {status1} vs {status2}). Resolve server status errors before optimizing content."

    # Parse query parameters
    p1 = urlparse(url1)
    p2 = urlparse(url2)
    same_path = (p1.netloc.lower() == p2.netloc.lower()) and (p1.path.rstrip('/') == p2.path.rstrip('/'))
    diff_query = bool(p1.query != p2.query)

    # 1. Parameter URL Duplication
    if same_path and diff_query and score >= 85.0:
        if same_canonical and canon1:
            return f"Parameter Duplication Managed: These URLs differ by query parameters but share canonical tag '{canon1}'. Search engines have clear indexing directives. Monitor crawl budget in Google Search Console."
        else:
            return "Parameter Duplication: URLs differ only by query parameters with identical/near-identical content. Add a self-referential canonical tag pointing to the clean base URL or handle parameters via robots.txt/sitemaps."

    # 2. Both declare the same canonical target
    if same_canonical and canon1:
        return f"Canonical Target Configured: Both pages point to '{canon1}'. Duplicate content is technically handled, but check internal linking to ensure you link directly to the preferred canonical URL."

    # 3. Cross-canonical pointing
    canon_status = pair.get('canonical_status')
    if canon_status == 'points_to_pair':
        return "Cross-Page Canonical: One page explicitly points its canonical tag to the other. Ensure the canonical target is 200 OK and indexable, and verify that internal navigation references the primary URL."

    # 4. Thin content warning
    if words1 < 120 and words2 < 120 and score >= 70.0:
        return f"Thin Content Duplicate Risk: Both pages have minimal unique text ({words1} and {words2} words). Shared boilerplate (menus, legal text) may be inflating similarity. Expand primary body copy or apply 'noindex' if low value."

    # 5. Exact duplicate with missing canonicals
    if classification == "Exact content duplicate":
        if not canon1 and not canon2:
            return "High Priority Consolidation: 100% identical body content with no canonical tags specified. Select the preferred version, implement a 301 redirect if one is redundant, or add a rel='canonical' tag to prevent split link equity."
        elif not canon1 or not canon2:
            missing_url = url1 if not canon1 else url2
            return f"Canonical Gap: 100% duplicate content, but '{missing_url}' is missing a canonical tag. Add a canonical tag pointing to the designated primary page."
        else:
            return f"Conflicting Canonicals: 100% duplicate content, yet both pages declare different canonical tags ('{canon1}' vs '{canon2}'). Unify them to avoid indexing confusion."

    # 6. Near duplicate (85%+)
    if classification == "Near duplicate":
        if title_match or h1_match:
            return f"Near-Duplicate Cannibalization ({score}%): Pages have nearly identical content and matching titles/headings. Risk of ranking cannibalization. Consolidate into a single authoritative page, or substantially differentiate their content."
        else:
            return f"High Content Overlap ({score}%): These pages share substantial text. If they target distinct user intents (e.g. regional locations or product variants), enrich each with unique localized details. If intents are identical, consolidate."

    # 7. Potential duplicate (70% - 84.9%)
    if classification == "Potential duplicate":
        if title_match or h1_match:
            return f"Keyword Overlap ({score}%): Similar headings/title with moderate body overlap. Review whether both pages are competing for the same organic keywords."
        else:
            return f"Moderate Similarity ({score}%): Pages share common phrasing. Acceptable if serving distinct user purposes; review to ensure adequate unique value on both pages."

    # 8. Low similarity
    return "Low Risk: Similarity is below threshold. Pages are sufficiently unique for search engines."
