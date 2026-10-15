import io
import csv
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

# ZeroGPU compatibility for Hugging Face Spaces
try:
    import spaces
    import gradio as gr
    HAS_ZEROGPU = True
except ImportError:
    HAS_ZEROGPU = False

from job_manager import JobManager
from test_server import test_app

app = FastAPI(
    title="SEO Duplicate-Page Detection API",
    description="Backend API for crawling, comparing, and identifying duplicate and near-duplicate pages.",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the mock test server under /test-pages for convenient testing
app.mount("/test-pages", test_app)

if HAS_ZEROGPU:
    @spaces.GPU(duration=60)
    def _hf_gpu_ping(status_msg: str):
        return f"SEO Duplicate Detector Backend is Active: {status_msg}"

    with gr.Blocks(title="SEO Duplicate URL Detector") as _hf_demo:
        gr.Markdown("### 🚀 SEO Duplicate-Page Detection Backend API is Running!")
        gr.Markdown("Interactive Swagger API Documentation: [Open /docs](/docs)")
        _txt_in = gr.Textbox(label="Status Ping", value="ready")
        _txt_out = gr.Textbox(label="Backend Response")
        _btn = gr.Button("Test Backend Connection")
        _btn.click(fn=_hf_gpu_ping, inputs=_txt_in, outputs=_txt_out)

    app = gr.mount_gradio_app(app, _hf_demo, path="/")
else:
    @app.get("/", include_in_schema=False)
    def root():
        """Redirect root path to interactive OpenAPI docs"""
        return RedirectResponse(url="/docs")

job_manager = JobManager()

class AnalyzeRequest(BaseModel):
    urls: List[str] = Field(..., description="List of URLs to crawl and analyze")
    user_topics: Optional[List[str]] = Field(default=None, description="Optional manual target topics/keywords for clustering")
    near_threshold: float = Field(default=85.0, ge=50.0, le=100.0)
    potential_threshold: float = Field(default=70.0, ge=40.0, le=95.0)
    respect_robots: bool = Field(default=True)
    allow_local_for_testing: bool = Field(default=False)

def extract_urls_from_text(text: str) -> List[str]:
    """Extracts and strips valid URL strings from text lines."""
    lines = text.splitlines()
    urls = []
    for line in lines:
        cleaned = line.strip().strip('"').strip("'")
        if cleaned and not cleaned.startswith('#'):
            # Basic validation: must have http/https or domain shape
            if cleaned.startswith(('http://', 'https://')) or ('.' in cleaned and '/' in cleaned):
                urls.append(cleaned)
    return urls

def extract_urls_from_csv(csv_content: str) -> List[str]:
    """Finds URLs in CSV data by inspecting columns."""
    urls = []
    reader = csv.reader(io.StringIO(csv_content))
    for row in reader:
        for cell in row:
            val = cell.strip()
            if val.startswith(('http://', 'https://')):
                urls.append(val)
                break
    return urls

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "SEO Duplicate Detection System"}

@app.get("/api/sample-urls")
def get_sample_urls():
    """
    Returns pre-configured test URLs that demonstrate all duplicate scenarios
    using the integrated test server.
    """
    base = "http://127.0.0.1:8000/test-pages"
    return {
        "description": "Pre-configured test suite showcasing exact duplicates, near duplicates, parameter URLs, heading conflicts, canonicals, and errors.",
        "sample_topics": [
            "Technical SEO Audits",
            "Commercial Roofing Services",
            "Digital Marketing Strategy",
            "Audio & Headphones Guide"
        ],
        "urls": [
            f"{base}/page/exact-a",
            f"{base}/page/exact-b",
            f"{base}/page/near-dup-1",
            f"{base}/page/near-dup-2",
            f"{base}/page/similar-headings-1",
            f"{base}/page/similar-headings-2",
            f"{base}/page/distinct-content",
            f"{base}/page/param-base",
            f"{base}/page/param-variant?sort=price_asc&ref=sidebar",
            f"{base}/page/redirect-start",
            f"{base}/page/http-404-broken",
            f"{base}/page/blocked-by-robots"
        ]
    }

@app.post("/api/analyze")
def start_analysis_json(req: AnalyzeRequest):
    raw_urls = [u.strip() for u in req.urls if u.strip()]
    if not raw_urls:
        raise HTTPException(status_code=400, detail="Please submit at least one valid URL.")

    # Auto-allow local testing if URLs target localhost/127.0.0.1
    allow_local = req.allow_local_for_testing
    if any("127.0.0.1" in u or "localhost" in u for u in raw_urls):
        allow_local = True

    job_id = job_manager.create_job(
        urls=raw_urls,
        near_threshold=req.near_threshold,
        potential_threshold=req.potential_threshold,
        respect_robots=req.respect_robots,
        allow_local_for_testing=allow_local,
        user_topics=req.user_topics
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "total_urls_submitted": len(raw_urls)
    }

@app.post("/api/analyze/upload")
async def start_analysis_upload(
    file: UploadFile = File(...),
    user_topics: Optional[str] = Form(None),
    near_threshold: float = Form(85.0),
    potential_threshold: float = Form(70.0),
    respect_robots: bool = Form(True),
    allow_local_for_testing: bool = Form(False)
):
    content = await file.read()
    filename = (file.filename or "").lower()

    try:
        text_content = content.decode('utf-8', errors='replace')
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read uploaded file as text.")

    if filename.endswith('.csv'):
        urls = extract_urls_from_csv(text_content)
    else:
        urls = extract_urls_from_text(text_content)

    if not urls:
        raise HTTPException(status_code=400, detail="No valid URLs found in the uploaded file.")

    allow_local = allow_local_for_testing
    if any("127.0.0.1" in u or "localhost" in u for u in urls):
        allow_local = True

    parsed_topics = None
    if user_topics:
        parsed_topics = [t.strip() for t in user_topics.replace(',', '\n').splitlines() if t.strip()]

    job_id = job_manager.create_job(
        urls=urls,
        near_threshold=near_threshold,
        potential_threshold=potential_threshold,
        respect_robots=respect_robots,
        allow_local_for_testing=allow_local,
        user_topics=parsed_topics
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "total_urls_submitted": len(urls)
    }

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    return {
        "job_id": job['job_id'],
        "status": job['status'],
        "progress": job['progress'],
        "results": job.get('results'),
        "error": job.get('error')
    }

@app.get("/api/jobs/{job_id}/diff")
def get_job_diff(job_id: str, pair_id: str = Query(..., description="ID of the pair to compare")):
    diff = job_manager.get_pair_diff(job_id, pair_id)
    if not diff:
        raise HTTPException(status_code=404, detail="Pair comparison not found or job incomplete.")
    return diff

@app.get("/api/jobs/{job_id}/export")
def export_job_csv(job_id: str):
    job = job_manager.get_job(job_id)
    if not job or not job.get('results'):
        raise HTTPException(status_code=400, detail="Job results are not ready for export.")

    results = job['results']
    pairs = results.get('pairs', [])
    clusters = results.get('clusters', [])

    # Map each URL to its cluster ID
    url_to_cluster = {}
    for c in clusters:
        for member in c['members']:
            url_to_cluster[member] = c['cluster_id']

    output = io.StringIO()
    # Excel compatibility: write UTF-8 BOM
    output.write('\ufeff')

    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "Group ID",
        "Pair ID",
        "URL 1",
        "URL 2",
        "Similarity Score (%)",
        "Duplicate Classification",
        "Title 1",
        "Title 2",
        "Title Match",
        "H1 1",
        "H1 2",
        "H1 Match",
        "Canonical URL 1",
        "Canonical URL 2",
        "Same Canonical Tag",
        "HTTP Status 1",
        "HTTP Status 2",
        "Word Count 1",
        "Word Count 2",
        "Recommended SEO Action"
    ])

    for p in pairs:
        group_id = url_to_cluster.get(p['url1']) or url_to_cluster.get(p['url2']) or "Ungrouped"
        writer.writerow([
            group_id,
            p.get('pair_id', ''),
            p.get('url1', ''),
            p.get('url2', ''),
            f"{p.get('similarity_score', 0):.1f}%",
            p.get('classification', ''),
            p.get('title1', ''),
            p.get('title2', ''),
            "Yes" if p.get('title_match') else "No",
            " | ".join(p.get('h1_1', [])),
            " | ".join(p.get('h1_2', [])),
            "Yes" if p.get('h1_match') else "No",
            p.get('canonical1') or "None",
            p.get('canonical2') or "None",
            "Yes" if p.get('same_canonical') else "No",
            p.get('status_code1') or "Error",
            p.get('status_code2') or "Error",
            p.get('word_count1', 0),
            p.get('word_count2', 0),
            p.get('recommended_action', '')
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=seo_duplicate_report_{job_id[:8]}.csv"
        }
    )

@app.get("/api/jobs/{job_id}/export-actions")
def export_actions_csv(job_id: str):
    job = job_manager.get_job(job_id)
    if not job or not job.get('results'):
        raise HTTPException(status_code=400, detail="Job results are not ready for export.")

    results = job['results']
    plan = results.get('consolidation_plan', {})
    actions = plan.get('actions', [])

    output = io.StringIO()
    # Excel UTF-8 BOM
    output.write('\ufeff')

    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "Source URL",
        "Recommended Action",
        "Action Code",
        "Target URL",
        "Priority",
        "Cluster ID",
        "HTTP Status",
        "Word Count",
        "Reasoning & Target Rationale"
    ])

    for a in actions:
        writer.writerow([
            a.get('source_url', ''),
            a.get('action_label', ''),
            a.get('action', ''),
            a.get('target_url') or "N/A",
            a.get('priority', 'Medium'),
            a.get('cluster_id', ''),
            a.get('status_code') or "Error",
            a.get('word_count', 0),
            a.get('reason', '')
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=seo_action_plan_{job_id[:8]}.csv"
        }
    )

@app.get("/api/jobs/{job_id}/export-topic-clusters")
def export_topic_clusters_csv(job_id: str):
    job = job_manager.get_job(job_id)
    if not job or not job.get('results'):
        raise HTTPException(status_code=400, detail="Job results are not ready for export.")

    results = job['results']
    topic_data = results.get('topic_clusters', {})
    clusters = topic_data.get('clusters', [])

    output = io.StringIO()
    # Excel UTF-8 BOM
    output.write('\ufeff')

    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "Topic Cluster ID",
        "Target Topic",
        "Topic Source",
        "URL",
        "Role in Cluster",
        "Search Intent",
        "Recommended Action",
        "Action Code",
        "Target URL",
        "Similarity to Primary (%)",
        "HTTP Status",
        "Word Count",
        "Priority",
        "Topic Confidence",
        "SEO Reasoning & Intent Rationale"
    ])

    for c in clusters:
        cluster_source = "User Defined" if c.get('topic_source') == 'USER_DEFINED' else "AI Auto-Detected"
        for p in c.get('pages', []):
            writer.writerow([
                c.get('cluster_id', ''),
                c.get('topic', ''),
                cluster_source,
                p.get('url', ''),
                p.get('role', ''),
                p.get('search_intent', ''),
                p.get('action_label', ''),
                p.get('action', ''),
                p.get('target_url') or "N/A",
                f"{p.get('similarity_to_primary', 0):.1f}%" if p.get('similarity_to_primary') is not None else "100.0%",
                p.get('status_code') or "Error",
                p.get('word_count', 0),
                p.get('priority', 'Medium'),
                f"{p.get('topic_confidence', 0):.0f}%" if p.get('topic_confidence') else "N/A",
                p.get('reason', '')
            ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=seo_topic_clusters_{job_id[:8]}.csv"
        }
    )

if __name__ == "__main__":
    import os
    import uvicorn
    # Hugging Face Spaces routes traffic to port 7860 by default
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port)

