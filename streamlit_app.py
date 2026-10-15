import sys
import os
import io
import csv
import time
import pandas as pd
import streamlit as st

# Configure page layout and title
st.set_page_config(
    page_title="SEO Duplicate-Page Detection & Consolidation System",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add backend directory to sys.path so existing engines load directly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from crawler import WebCrawler
from duplicate_detector import DuplicateDetector
from recommendations import generate_pair_recommendation
from consolidation_engine import generate_consolidation_plan
from cluster_engine import analyze_topic_clusters
from diff_utils import get_detailed_pair_comparison
from url_utils import normalize_url

# Initialize session state
if "audit_results" not in st.session_state:
    st.session_state.audit_results = None
if "input_urls_text" not in st.session_state:
    st.session_state.input_urls_text = ""

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.title("⚙️ Audit Settings")
    st.markdown("Configure crawling, similarity thresholds, and clustering rules.")
    
    near_thresh = st.slider(
        "Near-Duplicate Threshold (%)",
        min_value=50.0,
        max_value=100.0,
        value=85.0,
        step=1.0,
        help="Pages with Jaccard similarity at or above this threshold are classified as Near Duplicates."
    )
    
    potential_thresh = st.slider(
        "Potential Duplicate Threshold (%)",
        min_value=40.0,
        max_value=95.0,
        value=70.0,
        step=1.0,
        help="Pages between this value and the near threshold are flagged as Potential Duplicates."
    )
    
    respect_robots = st.checkbox(
        "Respect Robots.txt",
        value=True,
        help="Automatically fetch, cache, and respect robots.txt crawl rules."
    )
    
    st.markdown("---")
    st.subheader("🎯 Target Topics / Keywords")
    user_topics_input = st.text_area(
        "Optional Topics (one per line)",
        placeholder="e.g.\nTechnical SEO\nEmergency Plumber London\nBest Running Shoes",
        help="Provide manual keywords to guide AI cluster and search intent classification."
    )
    
    st.markdown("---")
    st.subheader("🧪 Load Sample Scenarios")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("Parameter Duplicates", use_container_width=True):
            st.session_state.input_urls_text = "\n".join([
                "https://en.wikipedia.org/wiki/Search_engine_optimization",
                "https://en.wikipedia.org/wiki/Search_engine_optimization?utm_source=twitter",
                "https://en.wikipedia.org/wiki/Search_engine_optimization?utm_medium=social&ref=blog",
                "https://en.wikipedia.org/wiki/Web_crawler",
                "https://en.wikipedia.org/wiki/Web_crawler?utm_source=newsletter"
            ])
            st.rerun()
            
    with col_s2:
        if st.button("Clear Inputs", use_container_width=True):
            st.session_state.input_urls_text = ""
            st.session_state.audit_results = None
            st.rerun()

    st.markdown("---")
    st.caption("SEO Duplicate Detector • Powered by MinHash LSH, Disjoint-Set Union & Streamlit")

# ----------------- MAIN HEADER -----------------
st.title("🔎 SEO Duplicate-Page Detection & Consolidation System")
st.markdown(
    "A production-ready SEO audit tool for crawling website URLs, stripping boilerplate templates, "
    "computing exact and near-duplicate content similarity (using MinHash LSH), diagnosing canonical issues, "
    "and generating server-ready redirect syntax."
)

# ----------------- URL INPUT SECTION -----------------
st.subheader("📥 Input URLs for Crawling")

tab_paste, tab_upload = st.tabs(["📝 Paste URLs", "📁 Upload Sitemap / CSV"])

raw_urls = []

with tab_paste:
    pasted_text = st.text_area(
        "Enter URLs (one per line)",
        value=st.session_state.input_urls_text,
        height=160,
        placeholder="https://example.com/page-1\nhttps://example.com/page-2\nhttps://example.com/page-1?utm_source=social"
    )
    if pasted_text:
        raw_urls = [line.strip() for line in pasted_text.splitlines() if line.strip() and not line.strip().startswith("#")]

with tab_upload:
    uploaded_file = st.file_uploader("Upload .csv or .txt URL list", type=["csv", "txt"])
    if uploaded_file is not None:
        file_content = uploaded_file.read().decode("utf-8", errors="replace")
        if uploaded_file.name.endswith(".csv"):
            reader = csv.reader(io.StringIO(file_content))
            for row in reader:
                for cell in row:
                    val = cell.strip()
                    if val.startswith(("http://", "https://")):
                        raw_urls.append(val)
        else:
            for line in file_content.splitlines():
                val = line.strip()
                if val and not val.startswith("#"):
                    if not val.startswith(("http://", "https://")):
                        val = "https://" + val
                    raw_urls.append(val)

# Normalize and deduplicate URLs before crawling
unique_urls = []
seen_normalized = set()
for u in raw_urls:
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    norm = normalize_url(u)
    if norm not in seen_normalized:
        seen_normalized.add(norm)
        unique_urls.append(u)

# Metric summary pill
col_m1, col_m2, col_m3 = st.columns([2, 2, 4])
with col_m1:
    st.metric("Total URLs Submitted", len(raw_urls))
with col_m2:
    st.metric("Unique URLs to Crawl", len(unique_urls))
with col_m3:
    start_btn = st.button("🚀 Start Crawl & Duplicate Audit", type="primary", use_container_width=True, disabled=(len(unique_urls) == 0))

# ----------------- EXECUTION PIPELINE -----------------
if start_btn and len(unique_urls) > 0:
    st.session_state.audit_results = None
    
    parsed_topics = [t.strip() for t in user_topics_input.splitlines() if t.strip()] if user_topics_input else None

    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(unique_urls)
    
    def on_crawl_progress(completed: int, tot: int, current_url: str):
        pct = int((completed / max(1, tot)) * 100)
        progress_bar.progress(pct)
        status_text.markdown(f"**Stage 1/4: Crawling URL {completed} of {tot}** (`{current_url}`)")

    try:
        # 1. Crawl
        status_text.markdown("**Stage 1/4: Initializing polite crawler & SSRF shield...**")
        crawler = WebCrawler(
            respect_robots=respect_robots,
            allow_local_for_testing=True
        )
        crawled_pages = crawler.crawl_urls(unique_urls, progress_callback=on_crawl_progress)

        # 2. Duplicate Detection (MinHash + Shingles)
        status_text.markdown("**Stage 2/4: Generating MinHash 3-gram shingles & LSH index...**")
        detector = DuplicateDetector(
            near_threshold=near_thresh,
            potential_threshold=potential_thresh
        )
        analysis_result = detector.analyze(crawled_pages)

        # 3. Recommendations & Page Consolidation
        status_text.markdown("**Stage 3/4: Electing Master URLs & generating consolidation rules...**")
        for pair in analysis_result['pairs']:
            pair['recommended_action'] = generate_pair_recommendation(pair)

        consolidation_plan = generate_consolidation_plan(
            clusters=analysis_result['clusters'],
            pairs=analysis_result['pairs'],
            pages=analysis_result['pages']
        )
        analysis_result['consolidation_plan'] = consolidation_plan

        # 4. Topic Clustering
        status_text.markdown("**Stage 4/4: Multi-signal search intent and cluster analysis...**")
        topic_analysis = analyze_topic_clusters(
            pages=analysis_result['pages'],
            pairs=analysis_result['pairs'],
            user_topics=parsed_topics
        )
        analysis_result['topic_clusters'] = topic_analysis

        progress_bar.progress(100)
        status_text.success(f"✅ Audit Complete! Analyzed {total} pages and identified {len(analysis_result['pairs'])} duplicate pairs.")
        
        st.session_state.audit_results = analysis_result
        time.sleep(1)

    except Exception as e:
        status_text.error(f"❌ Crawl Error: {str(e)}")

# ----------------- RESULTS DASHBOARD -----------------
results = st.session_state.audit_results

if results:
    pairs = results.get('pairs', [])
    pages = results.get('pages', [])
    clusters = results.get('clusters', [])
    plan = results.get('consolidation_plan', {})
    actions = plan.get('actions', [])
    topic_data = results.get('topic_clusters', {})

    exact_dupes = [p for p in pairs if p.get('classification') == 'Exact Duplicate']
    near_dupes = [p for p in pairs if p.get('classification') == 'Near Duplicate']
    potential_dupes = [p for p in pairs if p.get('classification') == 'Potential Duplicate']

    st.markdown("---")
    
    # Navigation Tabs
    tab_overview, tab_pairs, tab_clusters, tab_redirects, tab_diff, tab_export = st.tabs([
        "📊 Executive Summary",
        "🔗 Duplicate Pairs",
        "🧩 Cluster Grouping",
        "🛠️ Server Redirects",
        "🔍 Visual Content Diff",
        "📥 CSV Reports"
    ])

    # 1. EXECUTIVE SUMMARY
    with tab_overview:
        st.subheader("Audit Overview & KPIs")
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("Pages Audited", len(pages))
        kpi2.metric("Exact Duplicates", len(exact_dupes))
        kpi3.metric("Near Duplicates", len(near_dupes))
        kpi4.metric("Potential Duplicates", len(potential_dupes))
        kpi5.metric("Duplicate Clusters", len(clusters))

        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            st.markdown("#### Classification Breakdown")
            chart_data = pd.DataFrame({
                "Category": ["Exact Duplicates", "Near Duplicates", "Potential Duplicates"],
                "Count": [len(exact_dupes), len(near_dupes), len(potential_dupes)]
            })
            st.bar_chart(chart_data.set_index("Category"))

        with col_c2:
            st.markdown("#### Master Consolidation Directives")
            action_counts = {}
            for a in actions:
                lbl = a.get('action_label', 'Unknown')
                action_counts[lbl] = action_counts.get(lbl, 0) + 1
            
            if action_counts:
                act_df = pd.DataFrame(list(action_counts.items()), columns=["Recommended Action", "Count"])
                st.dataframe(act_df, use_container_width=True, hide_index=True)
            else:
                st.info("No consolidation actions required. All pages appear sufficiently unique!")

    # 2. DUPLICATE PAIRS
    with tab_pairs:
        st.subheader("Identified Duplicate & Near-Duplicate Pairs")
        
        filter_col1, filter_col2 = st.columns([2, 4])
        with filter_col1:
            class_filter = st.selectbox(
                "Filter by Classification",
                options=["All", "Exact Duplicate", "Near Duplicate", "Potential Duplicate"]
            )
        with filter_col2:
            search_query = st.text_input("Search URLs in pairs", placeholder="e.g. london, guide, recipe")

        filtered_pairs = pairs
        if class_filter != "All":
            filtered_pairs = [p for p in filtered_pairs if p.get('classification') == class_filter]
        if search_query:
            q = search_query.lower()
            filtered_pairs = [p for p in filtered_pairs if q in p.get('url1', '').lower() or q in p.get('url2', '').lower()]

        if filtered_pairs:
            pairs_rows = []
            for p in filtered_pairs:
                pairs_rows.append({
                    "Pair ID": p.get('pair_id', ''),
                    "Similarity": f"{p.get('similarity_score', 0):.1f}%",
                    "Classification": p.get('classification', ''),
                    "URL 1": p.get('url1', ''),
                    "URL 2": p.get('url2', ''),
                    "Title Match": "Yes" if p.get('title_match') else "No",
                    "H1 Match": "Yes" if p.get('h1_match') else "No",
                    "Same Canonical": "Yes" if p.get('same_canonical') else "No",
                    "Recommendation": p.get('recommended_action', '')
                })
            st.dataframe(pd.DataFrame(pairs_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No pairs matched the selected filters.")

    # 3. CLUSTERS & WINNER ELECTION
    with tab_clusters:
        st.subheader("Disjoint-Set Union (DSU) Clusters & Winner Election")
        st.markdown(
            "Rather than viewing isolated pairs, pages are merged into cohesive duplicate clusters. "
            "The system evaluates URL cleanliness, canonical tags, status codes, and word count to elect the **Authoritative Master Winner**."
        )

        cluster_summary = plan.get('cluster_summary', [])
        if cluster_summary:
            for c in cluster_summary:
                with st.expander(f"🧩 Cluster: {c.get('cluster_id')} ({c.get('total_pages')} Pages) — Master: {c.get('master_url')}"):
                    col_w1, col_w2 = st.columns([1, 1])
                    with col_w1:
                        st.markdown(f"**👑 Master Pillar URL:**\n`{c.get('master_url')}`")
                        st.markdown(f"**Authority Score:** `{c.get('authority_score', 0)} / 100`")
                        reasons = c.get('election_reasons', [])
                        if reasons:
                            st.markdown("**Election Rationale:**")
                            for r in reasons:
                                st.markdown(f"- {r}")
                    with col_w2:
                        st.markdown("**Cluster Member Actions:**")
                        member_actions = [a for a in actions if a.get('cluster_id') == c.get('cluster_id')]
                        for ma in member_actions:
                            st.markdown(f"- **{ma.get('action_label')}**: `{ma.get('source_url')}` $\\rightarrow$ `{ma.get('target_url', 'N/A')}`")
        else:
            st.info("No clusters formed. All pages are distinct.")

    # 4. SERVER REDIRECT SYNTAX
    with tab_redirects:
        st.subheader("⚡ Ready-to-Copy Server Redirect Configurations")
        st.markdown("Copy and paste these optimized 301 redirect rules directly into your server configuration files:")

        redirect_actions = [a for a in actions if a.get('action') in ['REDIRECT_301', 'MERGE_AND_REDIRECT'] and a.get('target_url')]

        if redirect_actions:
            # Generate Apache .htaccess syntax
            apache_rules = ["# 301 Redirect Rules Generated by SEO Duplicate-Page Detection", "RewriteEngine On"]
            # Generate Nginx rewrite syntax
            nginx_rules = ["# Nginx Rewrite Rules Generated by SEO Duplicate-Page Detection"]
            # Generate Cloudflare Bulk CSV
            cf_rows = [["Source URL", "Target URL", "Status Code"]]

            for a in redirect_actions:
                src = a.get('source_url', '')
                tgt = a.get('target_url', '')
                apache_rules.append(f"Redirect 301 {src} {tgt}")
                nginx_rules.append(f"rewrite ^{src}$ {tgt} permanent;")
                cf_rows.append([src, tgt, "301"])

            tab_ap, tab_ng, tab_cf = st.tabs(["Apache (.htaccess)", "Nginx (nginx.conf)", "Cloudflare Bulk CSV"])

            with tab_ap:
                st.code("\n".join(apache_rules), language="apache")

            with tab_ng:
                st.code("\n".join(nginx_rules), language="nginx")

            with tab_cf:
                cf_output = io.StringIO()
                writer = csv.writer(cf_output)
                writer.writerows(cf_rows)
                st.download_button(
                    "Download Cloudflare Redirect CSV",
                    data=cf_output.getvalue(),
                    file_name="cloudflare_bulk_redirects.csv",
                    mime="text/csv"
                )
                st.dataframe(pd.DataFrame(cf_rows[1:], columns=cf_rows[0]), use_container_width=True)
        else:
            st.info("No 301 redirects needed for this crawl.")

    # 5. SIDE-BY-SIDE VISUAL DIFF
    with tab_diff:
        st.subheader("🔍 Side-by-Side Visual Content & Heading Diff")
        st.markdown("Inspect exact textual discrepancies, shared phrases, and metadata differences between duplicate pairs.")

        if pairs:
            pair_options = {f"{p.get('pair_id')} ({p.get('classification')} - {p.get('similarity_score', 0):.0f}%)": p for p in pairs}
            selected_label = st.selectbox("Select Duplicate Pair to Compare", options=list(pair_options.keys()))
            selected_pair = pair_options[selected_label]

            page_map = {p['original_url']: p for p in pages}
            p1 = page_map.get(selected_pair['url1'])
            p2 = page_map.get(selected_pair['url2'])

            if p1 and p2:
                diff_data = get_detailed_pair_comparison(p1, p2, selected_pair)

                col_diff1, col_diff2 = st.columns(2)
                with col_diff1:
                    st.markdown(f"### Page 1\n`{p1['original_url']}`")
                    st.markdown(f"**Title:** {p1.get('title') or 'None'}")
                    st.markdown(f"**Canonical:** `{p1.get('canonical') or 'None'}`")
                    st.markdown(f"**Word Count:** `{p1.get('word_count', 0)}`")
                    st.markdown(f"**H1 Tags:** `{', '.join(p1.get('h1', [])) or 'None'}`")

                with col_diff2:
                    st.markdown(f"### Page 2\n`{p2['original_url']}`")
                    st.markdown(f"**Title:** {p2.get('title') or 'None'}")
                    st.markdown(f"**Canonical:** `{p2.get('canonical') or 'None'}`")
                    st.markdown(f"**Word Count:** `{p2.get('word_count', 0)}`")
                    st.markdown(f"**H1 Tags:** `{', '.join(p2.get('h1', [])) or 'None'}`")

                st.markdown("---")
                st.subheader("Text Diff Highlights")
                c_u1, c_u2 = st.columns(2)
                with c_u1:
                    st.markdown(f"**Unique to Page 1 ({len(diff_data.get('unique_to_page1', []))} sentences):**")
                    u1_text = "\n\n".join(diff_data.get('unique_to_page1', []))
                    st.text_area("Page 1 Unique Sentences", value=u1_text if u1_text else "No unique text found.", height=200, disabled=True)

                with c_u2:
                    st.markdown(f"**Unique to Page 2 ({len(diff_data.get('unique_to_page2', []))} sentences):**")
                    u2_text = "\n\n".join(diff_data.get('unique_to_page2', []))
                    st.text_area("Page 2 Unique Sentences", value=u2_text if u2_text else "No unique text found.", height=200, disabled=True)

                st.markdown(f"**Shared Boilerplate / Duplicate Sentences ({len(diff_data.get('shared_sentences', []))} sentences):**")
                shared_text = "\n\n".join(diff_data.get('shared_sentences', []))
                st.text_area("Shared Content", value=shared_text if shared_text else "No shared sentences.", height=150, disabled=True)
        else:
            st.info("No pairs available for comparison.")

    # 6. CSV EXPORTS
    with tab_export:
        st.subheader("📥 Export Audit Reports (Excel UTF-8 BOM Compatible)")
        st.markdown("Download full reports for your SEO clients, engineering team, or spreadsheet analysis.")

        col_e1, col_e2, col_e3 = st.columns(3)

        # Full Audit CSV
        with col_e1:
            out_audit = io.StringIO()
            out_audit.write('\ufeff')
            writer = csv.writer(out_audit)
            writer.writerow([
                "Pair ID", "URL 1", "URL 2", "Similarity Score (%)", "Duplicate Classification",
                "Title 1", "Title 2", "Title Match", "H1 Match", "Same Canonical",
                "Word Count 1", "Word Count 2", "Recommended SEO Action"
            ])
            for p in pairs:
                writer.writerow([
                    p.get('pair_id', ''), p.get('url1', ''), p.get('url2', ''),
                    f"{p.get('similarity_score', 0):.1f}%", p.get('classification', ''),
                    p.get('title1', ''), p.get('title2', ''),
                    "Yes" if p.get('title_match') else "No",
                    "Yes" if p.get('h1_match') else "No",
                    "Yes" if p.get('same_canonical') else "No",
                    p.get('word_count1', 0), p.get('word_count2', 0),
                    p.get('recommended_action', '')
                ])
            st.download_button(
                "📥 Download Full Audit CSV",
                data=out_audit.getvalue(),
                file_name="seo_duplicate_pairs_report.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Action Plan CSV
        with col_e2:
            out_plan = io.StringIO()
            out_plan.write('\ufeff')
            writer = csv.writer(out_plan)
            writer.writerow([
                "Source URL", "Recommended Action", "Action Code", "Target URL",
                "Priority", "Cluster ID", "HTTP Status", "Word Count", "Reasoning & Rationale"
            ])
            for a in actions:
                writer.writerow([
                    a.get('source_url', ''), a.get('action_label', ''), a.get('action', ''),
                    a.get('target_url') or "N/A", a.get('priority', 'Medium'),
                    a.get('cluster_id', ''), a.get('status_code') or "200",
                    a.get('word_count', 0), a.get('reason', '')
                ])
            st.download_button(
                "📋 Download Action Plan CSV",
                data=out_plan.getvalue(),
                file_name="seo_consolidation_action_plan.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Topic Clusters CSV
        with col_e3:
            clusters_list = topic_data.get('clusters', [])
            out_topic = io.StringIO()
            out_topic.write('\ufeff')
            writer = csv.writer(out_topic)
            writer.writerow([
                "Topic Cluster ID", "Target Topic", "Topic Source", "URL", "Role in Cluster",
                "Search Intent", "Recommended Action", "Target URL", "Similarity to Primary (%)",
                "Word Count", "Priority", "SEO Reasoning & Intent Rationale"
            ])
            for c in clusters_list:
                src_label = "User Defined" if c.get('topic_source') == 'USER_DEFINED' else "AI Auto-Detected"
                for p in c.get('pages', []):
                    writer.writerow([
                        c.get('cluster_id', ''), c.get('topic', ''), src_label,
                        p.get('url', ''), p.get('role', ''), p.get('search_intent', ''),
                        p.get('action_label', ''), p.get('target_url') or "N/A",
                        f"{p.get('similarity_to_primary', 0):.1f}%" if p.get('similarity_to_primary') is not None else "100.0%",
                        p.get('word_count', 0), p.get('priority', 'Medium'), p.get('reason', '')
                    ])
            st.download_button(
                "🧩 Download Topic Clusters CSV",
                data=out_topic.getvalue(),
                file_name="seo_topic_clusters_report.csv",
                mime="text/csv",
                use_container_width=True
            )
