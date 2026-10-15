# SEO Duplicate-Page Detection System

A complete, production-ready SEO audit tool for crawling website pages, stripping boilerplate templates, computing exact and near-duplicate content similarity (using word shingles and MinHash LSH), diagnosing canonical issues, and generating actionable, evidence-based SEO recommendations.

---

## Architecture Overview

```
┌──────────────────────────────────────────────┐
│       Next.js 15 + TypeScript Frontend       │
│  (Port 3000: Dashboard, Diff Modal, Charts)  │
└──────────────────────┬───────────────────────┘
                       │ HTTP REST (JSON / CSV)
┌──────────────────────▼───────────────────────┐
│         Python FastAPI Crawler Backend       │
│  (Port 8000: Requests, BeautifulSoup, LSH)   │
├──────────────────────────────────────────────┤
│  • SSRF Shield (blocks internal IPs/cloud)   │
│  • Robots.txt Compliance Engine              │
│  • Semantic Article Text Extractor           │
│  • MinHash & Locality Sensitive Hashing      │
│  • Disjoint-Set Cluster Grouping             │
│  • Side-by-Side Sentence/Token Diff Engine   │
│  • SEO Evidence-Based Recommendation Engine  │
│  • Excel-Ready UTF-8 BOM CSV Exporter        │
└──────────────────────────────────────────────┘
```

---

## Features

1. **Flexible URL Input**:
   - Paste URLs (one per line).
   - Upload `.csv` or `.txt` sitemap files.
   - Automatic live URL counter and input deduplication.
   - Preserves content-altering query parameters while normalizing tracking parameters (`utm_*`, `gclid`).

2. **Secure, Polite Crawling**:
   - **SSRF Protection**: Prohibits loopback (`127.0.0.1`), private networks (`10.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12`), link-local metadata services (`169.254.169.254`), and non-HTTP protocols across every initial request and redirect hop.
   - **Robots.txt Parser**: Caches and respects site crawl rules.
   - **Size Limits & Timeouts**: 5MB streaming buffer limit and configurable timeouts prevent memory exhaustion or crawl hangs.

3. **Semantic Main Content Extraction**:
   - Removes navigation, header, footer, scripts, styles, sidebar ads, and cookie banners.
   - Prioritizes semantic HTML5 tags (`<main>`, `<article>`, `[role="main"]`) with fallback to high-density text containers.

4. **Scalable Duplicate Detection (MinHash + LSH)**:
   - **Exact Duplicate**: SHA-256 content hashing after text normalization.
   - **Near Duplicate**: Word shingling (3-grams) + MinHash (128 hash permutations) + Locality Sensitive Hashing (LSH). Avoids $O(N^2)$ comparisons on large crawls.
   - **Similarity Scoring**: Exact Jaccard similarity metric (0% - 100%).
   - **Heading & Metadata Auditing**: Compares Titles, H1s, and H2s.
   - **Canonical Tag Auditing**: Detects missing canonicals, conflicting canonicals, self-referential canonicals, and shared targets.

5. **Cluster & Grouping Analysis**:
   - Uses Disjoint Set Union (Union-Find) to group duplicate URLs into cohesive clusters rather than forcing you to sift through disconnected pairs.

6. **Advanced Consolidation & Action Plan Engine**:
   - **Authority-Based Winner Election**: Evaluates URL path cleanliness, canonical directives, HTTP health, and content depth to elect the authoritative "Master Pillar URL" for each duplicate group.
   - **Action Categorization**:
     - `301 Redirect`: For exact duplicates and parameter variations. Recommends the specific target URL and explains why it won.
     - `Merge & Redirect`: For near-duplicate pages that share core topics but contain distinct paragraphs/word counts that should be carried over into the master page before redirecting.
     - `Delete / 410 Gone`: Pruning low-value or thin pages (< 50 words) to conserve crawl budget.
     - `Canonicalize`: For legitimate shopping or filter variants that must remain live for users.
     - `Differentiate`: For regional or multi-location landing pages that share boilerplate templates.
   - **Server Redirect Syntax Generator**: Instantly generates ready-to-paste redirect configuration blocks for Apache (`.htaccess`), Nginx (`rewrite`), and Cloudflare Bulk Redirect CSVs.

7. **Side-by-Side Visual Diff**:
   - Interactive modal highlighting shared text, unique content to Page 1, unique content to Page 2, and heading/canonical discrepancies.

8. **Evidence-Based SEO Recommendations**:
   - Tailored guidance on 301 redirects, canonical tag consolidation, parameter management, thin-content boilerplate risks, and keyword cannibalization.

9. **Dual CSV Export**:
   - **Full Audit CSV**: Complete pair-by-pair similarity scores, word counts, and canonical tags.
   - **Action Plan CSV**: Direct mapping table with Source URL, Action, Target URL, Priority, and Rationale formatted with UTF-8 BOM (`\ufeff`) for Excel.

---

## Getting Started (Quick Run)

### Option 1: Double-Click Launcher (Windows)
Double-click `start.bat` in the root folder. It will automatically start both the Python backend (port 8000) and the Next.js frontend (port 3000).

### Option 2: Running from Terminal

#### 1. Start Backend:
```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```
- API is live at: `http://127.0.0.1:8000`
- Interactive OpenAPI docs at: `http://127.0.0.1:8000/docs`

#### 2. Start Frontend:
```powershell
cd frontend
npm run dev
```
- Dashboard is live at: `http://localhost:3000`

---

## Running the Automated Test Suite

A standalone test suite is provided to verify all SEO scenarios against live test pages:
- Exact content duplicates
- Near-duplicates with localized phrasing
- Similar headings with different body content
- Parameter URLs with canonical tags
- HTTP 404, 500, and robots.txt blocking
- Side-by-side diff generation
- UTF-8 BOM CSV export

Run tests anytime:
```powershell
cd backend
.\venv\Scripts\python.exe test_suite.py
```

---

## Production Deployment Recommendations

> **Important Note on Serverless**:
> Python crawlers should **not** run inside short-lived serverless functions (such as AWS Lambda or Vercel Serverless Functions) for large crawls. Web crawling requires sustained TCP connections, polite delays, and background thread execution that exceed typical serverless execution limits (10–15 seconds).

### Recommended Deployment Architecture:

1. **Frontend (Next.js)**:
   - Host on **Vercel**, **Cloudflare Pages**, or **Netlify**.
   - Configure environment variable `NEXT_PUBLIC_API_URL` pointing to your backend.

2. **Backend (Python / FastAPI)**:
   - Host on a persistent container service:
     - **Render**, **Railway**, or **Fly.io** (Easy, low-cost Docker containers).
     - **DigitalOcean App Platform** or **AWS Lightsail** ($5 - $10/month VPS).
   - For enterprise-scale crawls (10,000+ URLs), add **Celery** + **Redis** to queue background jobs and write results to PostgreSQL or S3.
