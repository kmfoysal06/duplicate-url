import uuid
import time
import threading
from typing import Dict, List, Optional
from crawler import WebCrawler
from duplicate_detector import DuplicateDetector
from recommendations import generate_pair_recommendation
from diff_utils import get_detailed_pair_comparison
from url_utils import normalize_url

class JobManager:
    """
    In-memory background job manager for managing crawl and duplicate detection tasks.
    Avoids requiring a separate Redis/Postgres database for the local MVP while providing
    real-time progress, cancellation, and thread safety.
    """
    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self.lock = threading.Lock()

    def create_job(
        self,
        urls: List[str],
        near_threshold: float = 85.0,
        potential_threshold: float = 70.0,
        respect_robots: bool = True,
        allow_local_for_testing: bool = False,
        user_topics: Optional[List[str]] = None
    ) -> str:
        job_id = str(uuid.uuid4())
        
        # Deduplicate identical input entries before crawling while preserving list of submitted URLs
        seen_normalized = set()
        deduped_urls = []
        for u in urls:
            norm = normalize_url(u)
            if norm not in seen_normalized:
                seen_normalized.add(norm)
                deduped_urls.append(u)

        clean_user_topics = [t.strip() for t in (user_topics or []) if t.strip()]

        with self.lock:
            self.jobs[job_id] = {
                'job_id': job_id,
                'status': 'pending',  # pending, crawling, analyzing, completed, failed
                'progress': {
                    'stage': 'Initializing',
                    'current': 0,
                    'total': len(deduped_urls),
                    'percent': 0,
                    'current_url': '',
                    'message': f'Preparing to analyze {len(deduped_urls)} unique URLs...'
                },
                'created_at': time.time(),
                'urls_submitted': urls,
                'urls_to_crawl': deduped_urls,
                'user_topics': clean_user_topics,
                'near_threshold': near_threshold,
                'potential_threshold': potential_threshold,
                'respect_robots': respect_robots,
                'allow_local_for_testing': allow_local_for_testing,
                'results': None,
                'error': None
            }

        # Spawn background processing thread
        thread = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
        thread.start()
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict]:
        with self.lock:
            return self.jobs.get(job_id)

    def _update_progress(self, job_id: str, stage: str, current: int, total: int, current_url: str, message: str):
        with self.lock:
            if job_id in self.jobs:
                percent = int((current / max(1, total)) * 100) if total > 0 else 0
                self.jobs[job_id]['progress'] = {
                    'stage': stage,
                    'current': current,
                    'total': total,
                    'percent': percent,
                    'current_url': current_url,
                    'message': message
                }

    def _run_job(self, job_id: str):
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return

        urls_to_crawl = job['urls_to_crawl']
        total = len(urls_to_crawl)

        try:
            # Stage 1: Crawling
            with self.lock:
                self.jobs[job_id]['status'] = 'crawling'

            crawler = WebCrawler(
                respect_robots=job['respect_robots'],
                allow_local_for_testing=job['allow_local_for_testing']
            )

            def on_crawl_progress(completed: int, tot: int, url: str):
                self._update_progress(
                    job_id,
                    stage='Crawling',
                    current=completed,
                    total=tot,
                    current_url=url,
                    message=f"Crawling page {completed} of {tot}..."
                )

            crawled_pages = crawler.crawl_urls(urls_to_crawl, progress_callback=on_crawl_progress)

            # Stage 2: Content Analysis & Similarity
            self._update_progress(
                job_id,
                stage='Analyzing',
                current=total,
                total=total,
                current_url='',
                message="Calculating MinHash shingles and analyzing duplicate content..."
            )
            with self.lock:
                self.jobs[job_id]['status'] = 'analyzing'

            detector = DuplicateDetector(
                near_threshold=job['near_threshold'],
                potential_threshold=job['potential_threshold']
            )
            analysis_result = detector.analyze(crawled_pages)

            # Stage 3: Generate SEO Recommendations & Consolidation Plan
            for pair in analysis_result['pairs']:
                pair['recommended_action'] = generate_pair_recommendation(pair)

            # Generate advanced page-level consolidation plan (Redirect, Merge, Delete, Canonicalize)
            from consolidation_engine import generate_consolidation_plan
            consolidation_plan = generate_consolidation_plan(
                clusters=analysis_result['clusters'],
                pairs=analysis_result['pairs'],
                pages=analysis_result['pages']
            )
            analysis_result['consolidation_plan'] = consolidation_plan

            # Stage 4: Multi-Signal Topic, Slug & Search Intent Cluster Analysis
            from cluster_engine import analyze_topic_clusters
            topic_analysis = analyze_topic_clusters(
                pages=analysis_result['pages'],
                pairs=analysis_result['pairs'],
                user_topics=job.get('user_topics')
            )
            analysis_result['topic_clusters'] = topic_analysis

            with self.lock:
                self.jobs[job_id]['status'] = 'completed'
                self.jobs[job_id]['results'] = analysis_result
                self.jobs[job_id]['progress'] = {
                    'stage': 'Completed',
                    'current': total,
                    'total': total,
                    'percent': 100,
                    'current_url': '',
                    'message': f"Analysis complete! Processed {total} pages."
                }

        except Exception as e:
            with self.lock:
                self.jobs[job_id]['status'] = 'failed'
                self.jobs[job_id]['error'] = str(e)
                self.jobs[job_id]['progress']['message'] = f"Failed: {str(e)}"

    def get_pair_diff(self, job_id: str, pair_id: str) -> Optional[Dict]:
        """Returns side-by-side diff data for a specific pair."""
        with self.lock:
            job = self.jobs.get(job_id)
            if not job or not job.get('results'):
                return None
            results = job['results']

        pairs = results.get('pairs', [])
        target_pair = next((p for p in pairs if p['pair_id'] == pair_id), None)
        if not target_pair:
            return None

        pages = {p['original_url']: p for p in results.get('pages', [])}
        p1 = pages.get(target_pair['url1'])
        p2 = pages.get(target_pair['url2'])

        if not p1 or not p2:
            return None

        return get_detailed_pair_comparison(p1, p2, target_pair)
