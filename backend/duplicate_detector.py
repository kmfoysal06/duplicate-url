import re
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from datasketch import MinHash, MinHashLSH
from url_utils import normalize_url

def tokenize_words(text: str) -> List[str]:
    """Tokenizes text into lowercase alphanumeric words."""
    if not text:
        return []
    return re.findall(r'\b\w+\b', text.lower())

def create_shingles(words: List[str], k: int = 3) -> Set[str]:
    """
    Creates k-shingles (n-grams of words).
    Falls back to smaller k if word count is low.
    """
    if not words:
        return set()
    n = len(words)
    actual_k = min(k, n)
    if actual_k <= 1:
        return set(words)
    shingles = set()
    for i in range(n - actual_k + 1):
        shingles.add(" ".join(words[i:i + actual_k]))
    return shingles

def compute_jaccard(set_a: Set[str], set_b: Set[str]) -> float:
    """Computes exact Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    if union == 0:
        return 0.0
    return intersection / union

class DisjointSetUnion:
    """Disjoint Set Union (Union-Find) for clustering duplicate pages."""
    def __init__(self, elements: List[str]):
        self.parent = {el: el for el in elements}
        self.rank = {el: 0 for el in elements}

    def find(self, i: str) -> str:
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: str, j: str):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            if self.rank[root_i] < self.rank[root_j]:
                self.parent[root_i] = root_j
            elif self.rank[root_i] > self.rank[root_j]:
                self.parent[root_j] = root_i
            else:
                self.parent[root_j] = root_i
                self.rank[root_i] += 1

class DuplicateDetector:
    def __init__(
        self,
        near_threshold: float = 85.0,
        potential_threshold: float = 70.0,
        shingle_k: int = 3,
        num_perm: int = 128
    ):
        self.near_threshold = near_threshold
        self.potential_threshold = potential_threshold
        self.shingle_k = shingle_k
        self.num_perm = num_perm

    def _compare_headings(self, list_a: List[str], list_b: List[str]) -> Tuple[float, bool]:
        """Compares two lists of headings, returning similarity percentage and exact match bool."""
        set_a = {h.lower().strip() for h in list_a if h.strip()}
        set_b = {h.lower().strip() for h in list_b if h.strip()}
        if not set_a and not set_b:
            return 100.0, True
        if not set_a or not set_b:
            return 0.0, False
        if set_a == set_b:
            return 100.0, True
        jaccard = len(set_a.intersection(set_b)) / len(set_a.union(set_b))
        return round(jaccard * 100.0, 1), False

    def _compare_titles(self, title_a: str, title_b: str) -> Tuple[float, bool]:
        """Compares two titles, returning similarity percentage and exact match bool."""
        ta = title_a.strip().lower()
        tb = title_b.strip().lower()
        if not ta and not tb:
            return 100.0, True
        if not ta or not tb:
            return 0.0, False
        if ta == tb:
            return 100.0, True
        tokens_a = set(tokenize_words(ta))
        tokens_b = set(tokenize_words(tb))
        if not tokens_a or not tokens_b:
            return 0.0, False
        score = len(tokens_a.intersection(tokens_b)) / len(tokens_a.union(tokens_b))
        return round(score * 100.0, 1), False

    def analyze(self, crawled_pages: List[Dict]) -> Dict:
        """
        Runs complete duplicate detection:
        1. Exact hash matching
        2. MinHash & LSH candidate generation to scale past O(N^2)
        3. Exact Jaccard similarity scoring
        4. Heading & Canonical comparison
        5. Cluster grouping with Union-Find
        6. Summary statistics
        """
        total_urls = len(crawled_pages)
        successful_pages = [p for p in crawled_pages if not p.get('error') and p.get('word_count', 0) > 0]
        failed_pages = [p for p in crawled_pages if p.get('error') or p.get('word_count', 0) == 0]

        # Map page by original_url
        page_by_url = {p['original_url']: p for p in crawled_pages}
        all_urls = [p['original_url'] for p in crawled_pages]

        # Step 1: Pre-calculate shingles and MinHashes for valid pages
        shingles_by_url: Dict[str, Set[str]] = {}
        minhash_by_url: Dict[str, MinHash] = {}
        hash_to_urls: Dict[str, List[str]] = defaultdict(list)

        # LSH index (threshold lower than potential_threshold so we don't miss border candidates)
        lsh_threshold = max(0.50, (self.potential_threshold - 10) / 100.0)
        lsh = MinHashLSH(threshold=lsh_threshold, num_perm=self.num_perm)

        for p in successful_pages:
            url = p['original_url']
            content_hash = p.get('content_hash')
            if content_hash:
                hash_to_urls[content_hash].append(url)

            words = tokenize_words(p.get('main_text', ''))
            shingles = create_shingles(words, k=self.shingle_k)
            shingles_by_url[url] = shingles

            m = MinHash(num_perm=self.num_perm)
            for s in shingles:
                m.update(s.encode('utf-8'))
            minhash_by_url[url] = m
            try:
                lsh.insert(url, m)
            except Exception:
                pass

        # Step 2: Identify candidate pairs
        candidate_pairs: Set[Tuple[str, str]] = set()

        # A: Add exact hash matches
        for content_hash, urls in hash_to_urls.items():
            if len(urls) > 1:
                for i in range(len(urls)):
                    for j in range(i + 1, len(urls)):
                        u1, u2 = sorted([urls[i], urls[j]])
                        candidate_pairs.add((u1, u2))

        # B: Query LSH for near candidates
        for url, m in minhash_by_url.items():
            matches = lsh.query(m)
            for match in matches:
                if match != url:
                    u1, u2 = sorted([url, match])
                    candidate_pairs.add((u1, u2))

        # If total successful pages is small (<= 25), do exhaustive comparison to guarantee 100% recall
        if len(successful_pages) <= 25:
            for i in range(len(successful_pages)):
                for j in range(i + 1, len(successful_pages)):
                    u1, u2 = sorted([successful_pages[i]['original_url'], successful_pages[j]['original_url']])
                    candidate_pairs.add((u1, u2))

        # Step 3: Evaluate Candidate Pairs
        evaluated_pairs: List[Dict] = []
        dsu = DisjointSetUnion(all_urls)

        for u1, u2 in candidate_pairs:
            p1 = page_by_url[u1]
            p2 = page_by_url[u2]

            # Content comparison
            content_exact_match = (
                bool(p1.get('content_hash')) and
                p1.get('content_hash') == p2.get('content_hash')
            )

            shingles_1 = shingles_by_url.get(u1, set())
            shingles_2 = shingles_by_url.get(u2, set())
            jaccard_score = compute_jaccard(shingles_1, shingles_2) * 100.0

            if content_exact_match:
                similarity_score = 100.0
            else:
                similarity_score = round(jaccard_score, 1)

            # Classify
            if similarity_score >= 100.0 or content_exact_match:
                classification = "Exact content duplicate"
            elif similarity_score >= self.near_threshold:
                classification = "Near duplicate"
            elif similarity_score >= self.potential_threshold:
                classification = "Potential duplicate"
            else:
                classification = "Low similarity"

            # Heading comparisons
            title_sim, title_match = self._compare_titles(p1.get('title', ''), p2.get('title', ''))
            h1_sim, h1_match = self._compare_headings(p1.get('h1', []), p2.get('h1', []))
            h2_sim, _ = self._compare_headings(p1.get('h2', []), p2.get('h2', []))

            # Canonical analysis
            canon1 = p1.get('canonical_url')
            canon2 = p2.get('canonical_url')
            same_canonical = bool(canon1 and canon2 and canon1.lower() == canon2.lower())
            
            p1_points_to_p2 = bool(canon1 and canon1.lower() == normalize_url(p2['final_url']).lower())
            p2_points_to_p1 = bool(canon2 and canon2.lower() == normalize_url(p1['final_url']).lower())
            cross_canonical = p1_points_to_p2 or p2_points_to_p1

            canonical_status = "none"
            if same_canonical:
                canonical_status = "identical_canonical"
            elif cross_canonical:
                canonical_status = "points_to_pair"
            elif canon1 and canon2:
                canonical_status = "different_canonical"
            elif canon1 or canon2:
                canonical_status = "missing_one_canonical"
            else:
                canonical_status = "missing_both"

            pair_id = f"{u1}__{u2}"
            pair_data = {
                'pair_id': pair_id,
                'url1': u1,
                'url2': u2,
                'similarity_score': similarity_score,
                'classification': classification,
                'title1': p1.get('title', ''),
                'title2': p2.get('title', ''),
                'title_similarity': title_sim,
                'title_match': title_match,
                'h1_1': p1.get('h1', []),
                'h1_2': p2.get('h1', []),
                'h1_similarity': h1_sim,
                'h1_match': h1_match,
                'h2_1': p1.get('h2', []),
                'h2_2': p2.get('h2', []),
                'h2_similarity': h2_sim,
                'canonical1': canon1,
                'canonical2': canon2,
                'same_canonical': same_canonical,
                'canonical_status': canonical_status,
                'status_code1': p1.get('status_code'),
                'status_code2': p2.get('status_code'),
                'word_count1': p1.get('word_count', 0),
                'word_count2': p2.get('word_count', 0),
                'recommended_action': ''  # Populated by SEO recommendation engine
            }

            evaluated_pairs.append(pair_data)

            # Union into cluster if similarity meets duplicate threshold
            if similarity_score >= self.potential_threshold:
                dsu.union(u1, u2)

        # Sort pairs descending by similarity score
        evaluated_pairs.sort(key=lambda x: x['similarity_score'], reverse=True)

        # Step 4: Build Clusters / Groups
        clusters_map: Dict[str, List[str]] = defaultdict(list)
        for u in all_urls:
            root = dsu.find(u)
            clusters_map[root].append(u)

        duplicate_clusters = []
        cluster_index = 1
        for root, members in clusters_map.items():
            if len(members) > 1:
                # Find member pairs inside this cluster
                cluster_pairs = [
                    p for p in evaluated_pairs
                    if p['url1'] in members and p['url2'] in members and p['similarity_score'] >= self.potential_threshold
                ]
                
                # Determine highest classification within cluster
                highest_class = "Potential duplicate"
                max_score = 0.0
                for cp in cluster_pairs:
                    if cp['similarity_score'] > max_score:
                        max_score = cp['similarity_score']
                    if cp['classification'] == "Exact content duplicate":
                        highest_class = "Exact content duplicate"
                    elif cp['classification'] == "Near duplicate" and highest_class != "Exact content duplicate":
                        highest_class = "Near duplicate"

                duplicate_clusters.append({
                    'cluster_id': f"Group {cluster_index}",
                    'highest_classification': highest_class,
                    'highest_similarity': max_score,
                    'member_count': len(members),
                    'members': members,
                    'pairs_count': len(cluster_pairs)
                })
                cluster_index += 1

        # Step 5: Summary Statistics
        exact_groups = sum(1 for c in duplicate_clusters if c['highest_classification'] == "Exact content duplicate")
        near_groups = sum(1 for c in duplicate_clusters if c['highest_classification'] == "Near duplicate")
        potential_groups = sum(1 for c in duplicate_clusters if c['highest_classification'] == "Potential duplicate")

        # Count pages sharing canonicals
        canonical_target_counts = defaultdict(int)
        for p in crawled_pages:
            canon = p.get('canonical_url')
            if canon:
                canonical_target_counts[canon.lower()] += 1
        pages_sharing_canonicals = sum(count for count in canonical_target_counts.values() if count > 1)

        summary = {
            'total_urls_submitted': total_urls,
            'successfully_crawled': len(successful_pages),
            'failed_urls': len(failed_pages),
            'exact_duplicate_groups': exact_groups,
            'near_duplicate_groups': near_groups,
            'potential_duplicate_groups': potential_groups,
            'pages_sharing_canonicals': pages_sharing_canonicals,
            'total_duplicate_pairs': len([p for p in evaluated_pairs if p['similarity_score'] >= self.potential_threshold]),
            'evaluated_pairs_count': len(evaluated_pairs)
        }

        return {
            'summary': summary,
            'clusters': duplicate_clusters,
            'pairs': evaluated_pairs,
            'pages': crawled_pages
        }
