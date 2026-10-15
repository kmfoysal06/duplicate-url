import re
from collections import defaultdict
from urllib.parse import urlparse
from typing import List, Dict, Optional, Tuple, Set

from topic_intent_detector import (
    detect_search_intent,
    extract_primary_topic,
    calculate_slug_similarity,
    match_page_to_user_topics
)
from duplicate_detector import DisjointSetUnion
from consolidation_engine import calculate_page_authority_score
from url_utils import normalize_url

def analyze_topic_clusters(
    pages: List[Dict],
    pairs: List[Dict],
    user_topics: Optional[List[str]] = None
) -> Dict:
    """
    Groups URLs into Topic & Intent Clusters based on:
    1. User-Provided Topics (if supplied) or Auto-Extracted Topics
    2. Content text similarity (MinHash Jaccard)
    3. URL slug and naming similarity
    4. Search intent and keyword overlap

    Then performs a cluster-level multi-factor SEO analysis:
    - Search intent classification & intent conflicts
    - Primary URL election based on authority and content depth
    - Action recommendation per page:
      * KEEP_PRIMARY
      * 301_REDIRECT
      * MERGE_CONTENT
      * DELETE_OR_PRUNE
      * KEEP_SEPARATE
      * IMPROVE_CONTENT
    """
    total_pages = len(pages)
    if total_pages == 0:
        return {'clusters': [], 'summary': {}}

    clean_user_topics = [t.strip() for t in (user_topics or []) if t.strip()]

    page_map = {p['original_url']: p for p in pages}
    all_urls = [p['original_url'] for p in pages]

    # Step 1: Enrich every page with Topic, Intent, and Slug tokens
    for p in pages:
        title = p.get('title', '')
        h1 = p.get('h1', [])
        body = p.get('main_text', '')
        url = p.get('original_url', '')

        intent, conf = detect_search_intent(title, h1, body, url)
        p['search_intent'] = intent
        p['intent_confidence'] = conf

        # If user supplied topics, evaluate match against user topics first
        matched_user_topic = None
        user_conf = 0.0
        if clean_user_topics:
            matched_user_topic, user_conf = match_page_to_user_topics(p, clean_user_topics)

        if matched_user_topic:
            p['primary_topic'] = matched_user_topic
            p['topic_source'] = 'USER_DEFINED'
            p['topic_confidence'] = user_conf
        else:
            p['primary_topic'] = extract_primary_topic(title, h1, body)
            p['topic_source'] = 'AUTO_DETECTED'
            p['topic_confidence'] = 65.0

    # Build pair lookup for quick access
    pair_map = {}
    for pair in pairs:
        pair_map[(pair['url1'], pair['url2'])] = pair
        pair_map[(pair['url2'], pair['url1'])] = pair

    # Step 2: Multi-Signal Clustering with Disjoint Set Union
    dsu = DisjointSetUnion(all_urls)

    for i in range(len(pages)):
        p1 = pages[i]
        u1 = p1['original_url']

        for j in range(i + 1, len(pages)):
            p2 = pages[j]
            u2 = p2['original_url']

            # Signal 1: Content Similarity
            pair = pair_map.get((u1, u2))
            content_sim = pair.get('similarity_score', 0.0) if pair else 0.0

            # Signal 2: URL Slug Similarity
            slug_sim = calculate_slug_similarity(u1, u2)

            # Signal 3: Shared Topic Alignment
            same_topic = bool(
                p1['primary_topic'] and
                p2['primary_topic'] and
                p1['primary_topic'].lower() == p2['primary_topic'].lower()
            )

            # Signal 4: Title token overlap
            t1_words = set(re.findall(r'\b[a-z]{3,}\b', p1.get('title', '').lower()))
            t2_words = set(re.findall(r'\b[a-z]{3,}\b', p2.get('title', '').lower()))
            title_sim = 0.0
            if t1_words and t2_words:
                title_sim = len(t1_words.intersection(t2_words)) / len(t1_words.union(t2_words)) * 100.0

            # Clustering Rule:
            # Connect if:
            # - Content similarity >= 70% (content duplicate), OR
            # - High URL slug similarity (>= 60%), OR
            # - Matching primary topic + (slug_sim >= 35% or content_sim >= 35%), OR
            # - Title similarity >= 50%
            should_cluster = (
                content_sim >= 70.0 or
                slug_sim >= 60.0 or
                (same_topic and (slug_sim >= 35.0 or content_sim >= 35.0)) or
                title_sim >= 50.0
            )

            if should_cluster:
                dsu.union(u1, u2)

    # Step 3: Group URLs by cluster root
    root_to_members = defaultdict(list)
    for u in all_urls:
        root = dsu.find(u)
        root_to_members[root].append(u)

    # Step 4: Analyze each cluster and generate recommendations
    analyzed_clusters = []
    cluster_idx = 1

    total_redirects = 0
    total_merges = 0
    total_prunes = 0
    total_separate = 0
    total_improve = 0
    total_primaries = 0

    for root, members in root_to_members.items():
        # Even single-page clusters can be reported or focus on multi-page clusters
        cluster_pages = [page_map[u] for u in members if u in page_map]
        if not cluster_pages:
            continue

        # Determine dominant topic for the cluster
        topic_counts = defaultdict(int)
        intent_counts = defaultdict(int)
        for cp in cluster_pages:
            topic_counts[cp['primary_topic']] += 1
            intent_counts[cp['search_intent']] += 1

        dominant_topic = max(topic_counts.items(), key=lambda x: x[1])[0]
        cluster_source = 'USER_DEFINED' if any(cp.get('topic_source') == 'USER_DEFINED' for cp in cluster_pages if cp.get('primary_topic') == dominant_topic) else 'AUTO_DETECTED'

        # Calculate authority scores for each member to elect Primary Winner URL
        scored_members = []
        for cp in cluster_pages:
            sc, reasons = calculate_page_authority_score(cp, pages)
            scored_members.append({
                'url': cp['original_url'],
                'page': cp,
                'score': sc,
                'reasons': reasons
            })

        scored_members.sort(key=lambda x: x['score'], reverse=True)
        primary_member = scored_members[0]
        primary_url = primary_member['url']
        primary_page = primary_member['page']

        # Determine recommendations for every page in this cluster
        page_recommendations = []

        # 1. Primary Page Action
        page_recommendations.append({
            'url': primary_url,
            'role': 'PRIMARY',
            'action': 'KEEP_PRIMARY',
            'action_label': 'Retain as Primary Master Page',
            'target_url': None,
            'title': primary_page.get('title', ''),
            'search_intent': primary_page.get('search_intent', 'Informational'),
            'topic_source': primary_page.get('topic_source', 'AUTO_DETECTED'),
            'topic_confidence': primary_page.get('topic_confidence', 70.0),
            'matched_topic': primary_page.get('primary_topic', dominant_topic),
            'status_code': primary_page.get('status_code'),
            'word_count': primary_page.get('word_count', 0),
            'priority': 'High',
            'reason': (
                f"Selected as the authoritative Master URL for '{dominant_topic}' "
                f"based on: {'; '.join(primary_member['reasons'][:3])}."
            ),
            'action_summary': "Primary URL to preserve and build authority around."
        })
        total_primaries += 1

        # 2. Secondary Pages Actions
        for sec in scored_members[1:]:
            sec_url = sec['url']
            sec_page = sec['page']

            # Compare against primary
            pair = pair_map.get((sec_url, primary_url)) or pair_map.get((primary_url, sec_url))
            content_sim = pair.get('similarity_score', 0.0) if pair else 0.0
            same_canon = pair.get('same_canonical', False) if pair else False

            sec_words = sec_page.get('word_count', 0)
            primary_words = primary_page.get('word_count', 0)
            sec_intent = sec_page.get('search_intent', 'Informational')
            primary_intent = primary_page.get('search_intent', 'Informational')
            has_params = bool(urlparse(sec_url).query)
            sec_status = sec_page.get('status_code')

            same_intent = (sec_intent == primary_intent)

            # --- DECISION TREE ---

            # A. Thin content (< 60 words) or HTTP Error -> Delete / Prune (410)
            if sec_words < 60 or (sec_status and sec_status >= 400):
                action = 'DELETE_OR_PRUNE'
                label = 'Delete or Return 410 Gone'
                target = None
                priority = 'High'
                reason = (
                    f"Page has thin content ({sec_words} words) or HTTP error ({sec_status}). "
                    f"It provides negligible search value and wastes crawl budget. Prune or return 410 Gone."
                )
                act_sum = "Remove URL from sitemaps/internal links and return 410 Gone."
                total_prunes += 1

            # B. Exact Duplicate (>=95%) or Parameter Variant -> 301 Redirect
            elif content_sim >= 95.0 or (has_params and content_sim >= 85.0):
                action = '301_REDIRECT'
                label = '301 Permanent Redirect'
                target = primary_url
                priority = 'High'
                reason = (
                    f"Identical or parameter-based duplicate ({content_sim}% overlap) competing for the same topic. "
                    f"Implement a 301 redirect to {primary_url} to consolidate link equity and eliminate keyword cannibalization."
                )
                act_sum = f"Redirect permanently to {primary_url}."
                total_redirects += 1

            # C. Distinct Search Intents -> Keep Separate
            elif not same_intent and content_sim < 75.0:
                action = 'KEEP_SEPARATE'
                label = 'Keep Separate (Different Intent)'
                target = None
                priority = 'Medium'
                reason = (
                    f"Serves a distinct search intent ('{sec_intent}' vs Master's '{primary_intent}'). "
                    f"Both pages target different user needs. Keep both live and add internal cross-links."
                )
                act_sum = f"Maintain independent page for {sec_intent} intent; cross-link with {primary_url}."
                total_separate += 1

            # D. High Overlap (70% - 94%) with Same Intent -> Merge Content & 301
            elif same_intent and content_sim >= 70.0 and sec_words >= 100:
                action = 'MERGE_CONTENT'
                label = 'Merge Content & 301 Redirect'
                target = primary_url
                priority = 'High'
                reason = (
                    f"Both pages target '{sec_intent}' intent for '{dominant_topic}' with {content_sim}% overlap. "
                    f"This page has ~{sec_words} words of valuable copy. Merge its unique sections into {primary_url} "
                    f"to create a single comprehensive pillar page, then 301 redirect this URL."
                )
                act_sum = f"Consolidate unique points into {primary_url}, then set 301 redirect."
                total_merges += 1

            # E. Low Depth / Overlapping Phrasing -> Improve Content
            else:
                action = 'IMPROVE_CONTENT'
                label = 'Improve & Differentiate Content'
                target = None
                priority = 'Medium'
                reason = (
                    f"Shares topical overlap with {primary_url} ({content_sim}%). To rank independently without "
                    f"splitting organic traffic, expand unique sections (e.g. add FAQs, localized case studies, "
                    f"or target secondary long-tail keywords)."
                )
                act_sum = "Differentiate content and add unique value to prevent cannibalization."
                total_improve += 1

            page_recommendations.append({
                'url': sec_url,
                'role': 'SECONDARY',
                'action': action,
                'action_label': label,
                'target_url': target,
                'title': sec_page.get('title', ''),
                'search_intent': sec_intent,
                'topic_source': sec_page.get('topic_source', 'AUTO_DETECTED'),
                'topic_confidence': sec_page.get('topic_confidence', 70.0),
                'matched_topic': sec_page.get('primary_topic', dominant_topic),
                'status_code': sec_status,
                'word_count': sec_words,
                'similarity_to_primary': content_sim,
                'priority': priority,
                'reason': reason,
                'action_summary': act_sum
            })

        # Cluster Metadata
        analyzed_clusters.append({
            'cluster_id': f"Topic Group {cluster_idx}",
            'topic': dominant_topic,
            'topic_source': cluster_source,
            'member_count': len(cluster_pages),
            'primary_url': primary_url,
            'search_intents': dict(intent_counts),
            'has_intent_conflict': any(count > 1 for count in intent_counts.values()),
            'pages': page_recommendations
        })
        cluster_idx += 1

    # Sort clusters: largest member count first
    analyzed_clusters.sort(key=lambda c: c['member_count'], reverse=True)

    summary = {
        'total_topic_clusters': len(analyzed_clusters),
        'total_pages_analyzed': total_pages,
        'total_primary_master_urls': total_primaries,
        'total_recommended_redirects': total_redirects,
        'total_recommended_merges': total_merges,
        'total_recommended_pruning': total_prunes,
        'total_keep_separate': total_separate,
        'total_improve_content': total_improve
    }

    return {
        'summary': summary,
        'clusters': analyzed_clusters
    }
