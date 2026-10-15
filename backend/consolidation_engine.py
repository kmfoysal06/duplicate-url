import re
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from url_utils import normalize_url

def calculate_page_authority_score(page: Dict, all_pages: List[Dict]) -> Tuple[float, List[str]]:
    """
    Computes an objective authority score to determine which page should be
    the 'Master / Winner' URL in a duplicate cluster.
    Returns (score, list_of_reasons).
    """
    score = 0.0
    reasons = []

    url = page.get('original_url', '')
    parsed = urlparse(url)
    status = page.get('status_code')
    words = page.get('word_count', 0)
    canon = page.get('canonical_url')
    h1 = page.get('h1', [])

    # 1. HTTP Status (Essential baseline)
    if status == 200:
        score += 35.0
        reasons.append("Returns healthy HTTP 200 OK status")
    elif status and 300 <= status < 400:
        score += 10.0
    else:
        score -= 50.0
        reasons.append(f"Unhealthy HTTP status ({status})")

    # 2. Canonical signals (Search engine directive alignment)
    # Check if other pages point their canonical tag to this URL
    canonical_references = 0
    norm_this_url = normalize_url(page.get('final_url') or url).lower()
    for other in all_pages:
        if other.get('original_url') != url:
            other_canon = (other.get('canonical_url') or "").lower()
            if other_canon and other_canon == norm_this_url:
                canonical_references += 1

    if canonical_references > 0:
        score += 30.0 + (canonical_references * 5.0)
        reasons.append(f"Target of {canonical_references} canonical tag(s) from other pages")
    elif canon and canon.lower() == norm_this_url:
        score += 15.0
        reasons.append("Declares valid self-referential canonical tag")
    elif not canon:
        reasons.append("Missing canonical tag")

    # 3. URL Architecture & Cleanliness
    # Shorter URLs with no query parameters are generally preferred canonical targets
    has_params = bool(parsed.query)
    if not has_params:
        score += 20.0
        reasons.append("Clean URL path without query parameters")
    else:
        score -= 15.0
        reasons.append("Contains query parameters (often secondary/variant URL)")

    # Avoid duplicate/copy slugs like -copy, -v2, _2
    if re.search(r'-(?:copy|v\d+|\d+|temp|bak|new)$', parsed.path, re.I):
        score -= 25.0
        reasons.append("URL slug appears to be a temporary or copy version")

    # Shorter path depth represents higher-tier page architecture
    path_segments = [p for p in parsed.path.split('/') if p]
    if len(path_segments) <= 2:
        score += 10.0
        reasons.append("Higher-tier architecture (fewer folder levels)")

    # 4. Content Depth & Structure
    if words >= 300:
        score += 20.0
        reasons.append(f"Substantial content depth ({words} words)")
    elif words >= 150:
        score += 10.0
        reasons.append(f"Moderate content length ({words} words)")
    elif words < 75:
        score -= 20.0
        reasons.append(f"Thin content ({words} words)")

    # Heading hierarchy
    if h1 and len(h1) == 1:
        score += 5.0
        reasons.append("Has single clean H1 heading")

    return score, reasons

def generate_consolidation_plan(
    clusters: List[Dict],
    pairs: List[Dict],
    pages: List[Dict]
) -> Dict:
    """
    Evaluates duplicate clusters and pairwise overlaps to generate an
    actionable consolidation plan:
    - 301 Redirects (with chosen Master URL and rationale)
    - Content Merges (with unique section extraction)
    - Prune / 410 Deletions (for thin/worthless pages)
    - Canonicalize Directives (for UX variants)
    - Content Differentiation (for regional/intent variations)
    """
    page_map = {p['original_url']: p for p in pages}
    pair_map = {(p['url1'], p['url2']): p for p in pairs}
    # Allow reverse pair lookup
    for p in pairs:
        pair_map[(p['url2'], p['url1'])] = p

    actions: List[Dict] = []
    processed_urls = set()

    for cluster in clusters:
        members = cluster.get('members', [])
        if len(members) <= 1:
            continue

        # Score all members in the cluster to elect the primary winner URL
        scored_members = []
        for u in members:
            p = page_map.get(u)
            if p:
                sc, reasons = calculate_page_authority_score(p, pages)
                scored_members.append({
                    'url': u,
                    'page': p,
                    'score': sc,
                    'reasons': reasons
                })

        scored_members.sort(key=lambda x: x['score'], reverse=True)
        winner = scored_members[0]
        winner_url = winner['url']
        winner_page = winner['page']

        # Record Winner action
        actions.append({
            'source_url': winner_url,
            'cluster_id': cluster['cluster_id'],
            'action': 'KEEP_PRIMARY',
            'action_label': 'Retain as Master Pillar Page',
            'target_url': None,
            'status_code': winner_page.get('status_code'),
            'word_count': winner_page.get('word_count', 0),
            'priority': 'High',
            'reason': f"Selected as the authoritative Master URL for {cluster['cluster_id']} because: {'; '.join(winner['reasons'][:3])}.",
            'details': {
                'winner_reasons': winner['reasons'],
                'authority_score': round(winner['score'], 1)
            }
        })
        processed_urls.add(winner_url)

        # Evaluate each secondary URL in the cluster against the winner
        for sec in scored_members[1:]:
            sec_url = sec['url']
            sec_page = sec['page']
            processed_urls.add(sec_url)

            # Find pairwise comparison with winner
            pair_data = pair_map.get((sec_url, winner_url)) or pair_map.get((winner_url, sec_url))
            similarity = pair_data.get('similarity_score', 0.0) if pair_data else cluster.get('highest_similarity', 0.0)

            sec_words = sec_page.get('word_count', 0)
            winner_words = winner_page.get('word_count', 0)
            sec_status = sec_page.get('status_code')
            has_params = bool(urlparse(sec_url).query)
            same_canon = pair_data.get('same_canonical', False) if pair_data else False

            # --- Decision Logic ---

            # Case 1: Thin content or HTTP Errors -> Delete / Prune (410)
            if sec_words < 50 or (sec_status and sec_status >= 400):
                actions.append({
                    'source_url': sec_url,
                    'cluster_id': cluster['cluster_id'],
                    'action': 'PRUNE_OR_DELETE',
                    'action_label': 'Delete or Return 410 Gone',
                    'target_url': None,
                    'status_code': sec_status,
                    'word_count': sec_words,
                    'priority': 'Medium',
                    'reason': f"Page has thin/empty main content ({sec_words} words) or HTTP error ({sec_status}). It dilutes site quality and crawl budget. Safe to prune or return 410 Gone.",
                    'details': {
                        'target_recommendation': 'Remove from internal links and sitemap; return 410 Gone.'
                    }
                })

            # Case 2: Exact duplicate (100%) or Parameter Duplication -> 301 Redirect
            elif similarity >= 95.0 or (has_params and similarity >= 85.0):
                actions.append({
                    'source_url': sec_url,
                    'cluster_id': cluster['cluster_id'],
                    'action': '301_REDIRECT',
                    'action_label': '301 Permanent Redirect',
                    'target_url': winner_url,
                    'status_code': sec_status,
                    'word_count': sec_words,
                    'priority': 'High',
                    'reason': f"Identical or parameter-based duplicate ({similarity}% similarity) of Master URL. Consolidate link equity and eliminate ranking cannibalization by implementing a 301 redirect to {winner_url}.",
                    'details': {
                        'why_target': f"Target '{winner_url}' was chosen because: {'; '.join(winner['reasons'][:2])}.",
                        'redirect_type': '301 Permanent Redirect'
                    }
                })

            # Case 3: Near duplicate with unique content sections (75% - 94.9%) -> Content Merge & 301
            elif 75.0 <= similarity < 95.0 and sec_words > 100:
                actions.append({
                    'source_url': sec_url,
                    'cluster_id': cluster['cluster_id'],
                    'action': 'MERGE_AND_REDIRECT',
                    'action_label': 'Merge Content & 301 Redirect',
                    'target_url': winner_url,
                    'status_code': sec_status,
                    'word_count': sec_words,
                    'priority': 'High',
                    'reason': f"High content overlap ({similarity}%), but this page contains ~{sec_words} words that may include distinct details. Merge any unique paragraphs into {winner_url} to create an authoritative pillar page, then 301 redirect.",
                    'details': {
                        'why_target': f"Master URL '{winner_url}' has stronger architecture and {winner_words} words.",
                        'merge_guidance': f"Copy unique points from {sec_url} into {winner_url}, then set 301 redirect."
                    }
                })

            # Case 4: Variant or faceted navigation -> Canonicalize
            elif same_canon or has_params:
                actions.append({
                    'source_url': sec_url,
                    'cluster_id': cluster['cluster_id'],
                    'action': 'CANONICALIZE',
                    'action_label': 'Add rel="canonical" Tag',
                    'target_url': winner_url,
                    'status_code': sec_status,
                    'word_count': sec_words,
                    'priority': 'Medium',
                    'reason': f"Faceted navigation or UX parameter variant ({similarity}% overlap). If needed for user filtering, keep active on-site but add `<link rel='canonical' href='{winner_url}' />`.",
                    'details': {
                        'canonical_target': winner_url
                    }
                })

            # Case 5: Regional / Intent Variation -> Differentiate
            else:
                actions.append({
                    'source_url': sec_url,
                    'cluster_id': cluster['cluster_id'],
                    'action': 'DIFFERENTIATE',
                    'action_label': 'Keep Both & Differentiate',
                    'target_url': None,
                    'status_code': sec_status,
                    'word_count': sec_words,
                    'priority': 'Low',
                    'reason': f"Moderate similarity ({similarity}%) likely due to shared website templates or service listings. Do NOT redirect if targeting different locations/audiences; instead, add unique local case studies and testimonials.",
                    'details': {
                        'advice': 'Expand unique localized content rather than deleting or redirecting.'
                    }
                })

    # Summary counts
    count_redirect = sum(1 for a in actions if a['action'] == '301_REDIRECT')
    count_merge = sum(1 for a in actions if a['action'] == 'MERGE_AND_REDIRECT')
    count_prune = sum(1 for a in actions if a['action'] == 'PRUNE_OR_DELETE')
    count_canonicalize = sum(1 for a in actions if a['action'] == 'CANONICALIZE')
    count_differentiate = sum(1 for a in actions if a['action'] == 'DIFFERENTIATE')
    count_primary = sum(1 for a in actions if a['action'] == 'KEEP_PRIMARY')

    # Generate server redirect snippets
    redirect_actions = [a for a in actions if a.get('target_url') and a['action'] in ('301_REDIRECT', 'MERGE_AND_REDIRECT')]
    nginx_rules = []
    apache_rules = []
    cloudflare_csv = ["source,destination,status_code"]

    for r in redirect_actions:
        src_path = urlparse(r['source_url']).path or '/'
        if urlparse(r['source_url']).query:
            src_path += '?' + urlparse(r['source_url']).query
        tgt = r['target_url']
        nginx_rules.append(f"rewrite ^{re.escape(src_path)}$ {tgt} permanent;")
        apache_rules.append(f"Redirect 301 \"{src_path}\" \"{tgt}\"")
        cloudflare_csv.append(f"\"{r['source_url']}\",\"{tgt}\",301")

    return {
        'summary': {
            'total_actions_recommended': len(actions),
            'to_redirect_301': count_redirect,
            'to_merge_and_redirect': count_merge,
            'to_prune_or_delete': count_prune,
            'to_canonicalize': count_canonicalize,
            'to_differentiate': count_differentiate,
            'primary_master_pages': count_primary
        },
        'actions': actions,
        'export_snippets': {
            'nginx': "\n".join(nginx_rules) if nginx_rules else "# No 301 redirect rules needed.",
            'apache': "\n".join(apache_rules) if apache_rules else "# No 301 redirect rules needed.",
            'cloudflare_csv': "\n".join(cloudflare_csv)
        }
    }
