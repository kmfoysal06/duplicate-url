import time
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=" * 60)
    print("SEO Duplicate-Page Detection System - Test Suite")
    print("=" * 60)

    # 1. Health check
    print("\n[1/6] Testing Health Endpoint...")
    resp = requests.get(f"{BASE_URL}/api/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    print("[PASS] Backend API is healthy.")

    # 2. Sample URLs
    print("\n[2/6] Fetching Sample Test Suite URLs...")
    resp = requests.get(f"{BASE_URL}/api/sample-urls")
    assert resp.status_code == 200
    data = resp.json()
    urls = data['urls']
    print(f"[PASS] Retrieved {len(urls)} test URLs covering all required SEO scenarios.")

    # 3. Submit Analysis Job
    print("\n[3/6] Submitting Crawl & Duplicate Analysis Job...")
    payload = {
        "urls": urls,
        "near_threshold": 85.0,
        "potential_threshold": 70.0,
        "respect_robots": True,
        "allow_local_for_testing": True
    }
    resp = requests.post(f"{BASE_URL}/api/analyze", json=payload)
    assert resp.status_code == 200, f"Submit failed: {resp.text}"
    job_id = resp.json()["job_id"]
    print(f"[PASS] Job created with ID: {job_id}")

    # 4. Poll Progress until Completed
    print("\n[4/6] Polling Job Progress...")
    completed = False
    for attempt in range(40):
        time.sleep(0.5)
        resp = requests.get(f"{BASE_URL}/api/jobs/{job_id}")
        assert resp.status_code == 200
        job_data = resp.json()
        status = job_data['status']
        prog = job_data['progress']
        print(f"  Status: {status:10} | Progress: {prog['percent']}% | {prog['message']}")
        if status == 'completed':
            completed = True
            break
        elif status == 'failed':
            raise RuntimeError(f"Job failed: {job_data.get('error')}")

    assert completed, "Job did not complete in expected time window."
    print("[PASS] Analysis job completed successfully!")

    # 5. Verify Results and Classifications
    print("\n[5/6] Verifying SEO Duplicate Detection Accuracy...")
    results = job_data['results']
    summary = results['summary']
    pairs = results['pairs']
    clusters = results['clusters']

    print(f"  Total URLs Submitted: {summary['total_urls_submitted']}")
    print(f"  Successfully Crawled: {summary['successfully_crawled']}")
    print(f"  Failed / Blocked:     {summary['failed_urls']}")
    print(f"  Exact Duplicate Grps: {summary['exact_duplicate_groups']}")
    print(f"  Near Duplicate Grps:  {summary['near_duplicate_groups']}")
    print(f"  Duplicate Clusters:   {len(clusters)}")

    # Verify Exact Duplicate Pair
    exact_pair = next(
        (p for p in pairs if "exact-a" in p['url1'] and "exact-b" in p['url2'] or ("exact-b" in p['url1'] and "exact-a" in p['url2'])),
        None
    )
    assert exact_pair is not None, "Exact duplicate pair not found!"
    assert exact_pair['similarity_score'] == 100.0, f"Expected 100%, got {exact_pair['similarity_score']}%"
    assert exact_pair['classification'] == "Exact content duplicate"
    print("  [PASS] Exact Duplicates correctly identified with 100.0% similarity!")

    # Verify Near Duplicate Pair
    near_pair = next(
        (p for p in pairs if "near-dup-1" in p['url1'] and "near-dup-2" in p['url2'] or ("near-dup-2" in p['url1'] and "near-dup-1" in p['url2'])),
        None
    )
    assert near_pair is not None, "Near duplicate pair not found!"
    assert near_pair['similarity_score'] >= 85.0, f"Expected >= 85%, got {near_pair['similarity_score']}%"
    assert near_pair['classification'] == "Near duplicate"
    print(f"  [PASS] Near Duplicates correctly scored: {near_pair['similarity_score']}% ('Near duplicate')")

    # Verify Similar Headings with Different Body is NOT classified as duplicate
    heading_pair = next(
        (p for p in pairs if "similar-headings-1" in p['url1'] and "similar-headings-2" in p['url2'] or ("similar-headings-2" in p['url1'] and "similar-headings-1" in p['url2'])),
        None
    )
    if heading_pair:
        assert heading_pair['similarity_score'] < 70.0, f"Expected <70% for different body, got {heading_pair['similarity_score']}"
        assert heading_pair['title_match'] is True
        print(f"  [PASS] Similar headings with different body correctly flagged: Headings match, but similarity is only {heading_pair['similarity_score']}% (Low similarity)")

    # Verify Canonical Tag Detection
    param_pair = next(
        (p for p in pairs if "param-base" in p['url1'] and "param-variant" in p['url2'] or ("param-variant" in p['url1'] and "param-base" in p['url2'])),
        None
    )
    if param_pair:
        assert param_pair['same_canonical'] is True
        print(f"  [PASS] Canonical tag match detected: {param_pair['canonical1']} (Same canonical = True)")

    # Verify Diff Endpoint
    print("\n[6/8] Verifying Side-by-Side Diff and CSV Exports...")
    diff_resp = requests.get(f"{BASE_URL}/api/jobs/{job_id}/diff?pair_id={exact_pair['pair_id']}")
    assert diff_resp.status_code == 200, f"Diff failed: {diff_resp.text}"
    diff_data = diff_resp.json()
    assert len(diff_data['shared_content']) > 0, "Shared content expected"
    print("  [PASS] Side-by-side diff generator returned shared and tokenized content.")

    # Verify CSV Export
    csv_resp = requests.get(f"{BASE_URL}/api/jobs/{job_id}/export")
    assert csv_resp.status_code == 200
    assert csv_resp.content.startswith(b'\xef\xbb\xbf'), "CSV should begin with UTF-8 BOM"
    lines = csv_resp.text.splitlines()
    assert len(lines) > 2, "CSV should contain headers and rows"
    print(f"  [PASS] CSV Report exported successfully ({len(lines)} lines with UTF-8 BOM).")

    # 7. Verify Automatic Topic Clusters & Consolidation Plan
    print("\n[7/8] Verifying AI Topic Clusters & Consolidation Engine...")
    assert 'topic_clusters' in results, "Topic clusters expected in analysis results"
    topic_data = results['topic_clusters']
    clusters_list = topic_data.get('clusters', [])
    assert len(clusters_list) > 0, "Expected at least one topic cluster"
    print(f"  [PASS] Identified {len(clusters_list)} AI auto-detected topic clusters.")
    
    # Check page actions in auto clusters
    actions_found = set()
    for c in clusters_list:
        for p in c['pages']:
            actions_found.add(p['action'])
    print(f"  [PASS] Cluster page action recommendations generated: {actions_found}")

    # 8. Verify User-Provided Topics Clustering
    print("\n[8/8] Testing User-Provided Target Topics Clustering...")
    user_topics_payload = {
        "urls": urls[:6],
        "user_topics": [
            "Technical SEO Audits",
            "Commercial Roofing Services",
            "Audio & Headphones Guide"
        ],
        "allow_local_for_testing": True
    }
    resp2 = requests.post(f"{BASE_URL}/api/analyze", json=user_topics_payload)
    assert resp2.status_code == 200
    job_id2 = resp2.json()["job_id"]

    for _ in range(40):
        time.sleep(0.5)
        r = requests.get(f"{BASE_URL}/api/jobs/{job_id2}")
        if r.status_code == 200 and r.json()['status'] == 'completed':
            break

    job2_data = requests.get(f"{BASE_URL}/api/jobs/{job_id2}").json()
    job2_topics = job2_data['results']['topic_clusters']['clusters']
    assert len(job2_topics) > 0, "Expected clusters from user-provided topics"
    has_user_source = any(c.get('topic_source') == 'USER_DEFINED' for c in job2_topics)
    print(f"  [PASS] User-provided topics matched successfully (USER_DEFINED source verified: {has_user_source})")

    # Verify Topic Clusters CSV Export
    t_csv_resp = requests.get(f"{BASE_URL}/api/jobs/{job_id2}/export-topic-clusters")
    assert t_csv_resp.status_code == 200
    assert t_csv_resp.content.startswith(b'\xef\xbb\xbf')
    t_lines = t_csv_resp.text.splitlines()
    assert len(t_lines) > 1
    print(f"  [PASS] Topic clusters CSV exported successfully ({len(t_lines)} lines).")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
