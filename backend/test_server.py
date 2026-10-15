from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, RedirectResponse

test_app = FastAPI(title="SEO Test Pages Server")

ARTICLE_BASE = """
<article>
    <h1>Technical SEO Audit: The Comprehensive 2026 Guide</h1>
    <p>A technical SEO audit evaluates the technical health and indexability of a website to identify barriers that prevent search engines from crawling, indexing, and ranking pages effectively.</p>
    <p>Core areas of analysis include site architecture, crawl depth, XML sitemaps, robots.txt directives, status codes, canonical link elements, duplicate content detection, structured data, mobile usability, and Core Web Vitals performance metrics.</p>
    <p>Duplicate content creates significant crawl budget wastage and keyword cannibalization when search engines cannot determine which URL represents the authoritative source for a query.</p>
    <p>By conducting regular automated audits, SEO professionals safeguard organic search visibility and ensure optimal search engine rendering.</p>
</article>
"""

@test_app.get("/robots.txt")
def robots_txt():
    return Response(
        content="User-agent: *\nDisallow: /page/blocked-by-robots\n",
        media_type="text/plain"
    )

@test_app.get("/page/exact-a", response_class=HTMLResponse)
def page_exact_a():
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Technical SEO Audit Guide 2026</title>
    <meta name="description" content="Comprehensive technical SEO audit guide.">
    <!-- No canonical tag declared -->
</head>
<body>
    <header><nav><a href="/">Home</a> | <a href="/about">About</a></nav></header>
    {ARTICLE_BASE}
    <footer>Copyright 2026 Acme Corp. All rights reserved.</footer>
</body>
</html>"""

@test_app.get("/page/exact-b", response_class=HTMLResponse)
def page_exact_b():
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Technical SEO Audit Guide 2026</title>
    <meta name="description" content="Comprehensive technical SEO audit guide.">
    <!-- No canonical tag declared -->
</head>
<body>
    <header><nav><a href="/">Home</a> | <a href="/contact">Contact</a></nav></header>
    {ARTICLE_BASE}
    <footer>Copyright 2026 Acme Corp. All rights reserved.</footer>
</body>
</html>"""

@test_app.get("/page/near-dup-1", response_class=HTMLResponse)
def page_near_dup_1():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Commercial Roofing Services in Denver, Colorado</title>
</head>
<body>
    <main>
        <h1>Expert Commercial Roofing Contractors in Denver</h1>
        <p>Our certified roofing team provides premium commercial roofing, roof repair, leak detection, and flat roof replacement for commercial properties throughout Denver, Colorado.</p>
        <p>We work with TPO, EPDM, metal roofing systems, and asphalt shingles with 24/7 rapid emergency repair response times.</p>
        <p>Every commercial roof installation comes with a comprehensive 20-year materials and labor warranty backed by certified master roofers.</p>
        <p>We strictly adhere to national safety standards, building codes, and municipal energy efficiency mandates for all industrial warehouses and retail centers.</p>
        <p>Our preventative maintenance agreements include semi-annual drone inspections, thermal infrared scanning, and complete drainage clearing to protect your property investment.</p>
        <p>Schedule your free Denver roof inspection and commercial estimate with our licensed local specialists today.</p>
    </main>
</body>
</html>"""

@test_app.get("/page/near-dup-2", response_class=HTMLResponse)
def page_near_dup_2():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Commercial Roofing Services in Boulder, Colorado</title>
</head>
<body>
    <main>
        <h1>Expert Commercial Roofing Contractors in Boulder</h1>
        <p>Our certified roofing team provides premium commercial roofing, roof repair, leak detection, and flat roof replacement for commercial properties throughout Boulder, Colorado.</p>
        <p>We work with TPO, EPDM, metal roofing systems, and asphalt shingles with 24/7 rapid emergency repair response times.</p>
        <p>Every commercial roof installation comes with a comprehensive 20-year materials and labor warranty backed by certified master roofers.</p>
        <p>We strictly adhere to national safety standards, building codes, and municipal energy efficiency mandates for all industrial warehouses and retail centers.</p>
        <p>Our preventative maintenance agreements include semi-annual drone inspections, thermal infrared scanning, and complete drainage clearing to protect your property investment.</p>
        <p>Schedule your free Boulder roof inspection and commercial estimate with our licensed local specialists today.</p>
    </main>
</body>
</html>"""

@test_app.get("/page/similar-headings-1", response_class=HTMLResponse)
def page_heading_1():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Mastering Digital Advertising Strategy</title>
</head>
<body>
    <article>
        <h1>Mastering Digital Advertising Strategy</h1>
        <h2>Maximizing Search Ads and Paid Media</h2>
        <p>Google Search Ads drive immediate high-intent customer acquisition through keyword bidding, ad extensions, target CPA optimization, and remarketing lists for search ads.</p>
        <p>Continuous negative keyword expansion and conversion tracking allow advertisers to achieve scalable return on ad spend (ROAS) across competitive search auctions.</p>
    </article>
</body>
</html>"""

@test_app.get("/page/similar-headings-2", response_class=HTMLResponse)
def page_heading_2():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Mastering Digital Advertising Strategy</title>
</head>
<body>
    <article>
        <h1>Mastering Digital Advertising Strategy</h1>
        <h2>Maximizing Search Ads and Paid Media</h2>
        <p>Short-form organic video on TikTok and Instagram Reels generates authentic viral engagement, audience affinity, and influencer partnerships without paying high cost-per-click fees.</p>
        <p>By leveraging trending sounds, community hooks, and user-generated testimonials, modern direct-to-consumer brands cultivate lasting social loyalty.</p>
    </article>
</body>
</html>"""

@test_app.get("/page/distinct-content", response_class=HTMLResponse)
def page_distinct():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Classic French Chocolate Ganache Recipe</title>
</head>
<body>
    <article>
        <h1>Classic French Chocolate Ganache Recipe</h1>
        <h2>Baking and Pastry Arts</h2>
        <p>To prepare an authentic velvety French chocolate ganache, gently heat heavy whipping cream to a simmer before pouring over finely chopped 70% bittersweet dark chocolate.</p>
        <p>Whisk smoothly from the center outward until a glossy emulsification forms. Cool at room temperature before frosting pastries, cakes, or piping delicate truffles.</p>
    </article>
</body>
</html>"""

@test_app.get("/page/param-base", response_class=HTMLResponse)
def page_param_base():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Wireless Noise-Cancelling Headphones Pro</title>
    <link rel="canonical" href="http://127.0.0.1:8001/page/param-base" />
</head>
<body>
    <main>
        <h1>Wireless Noise-Cancelling Headphones Pro</h1>
        <p>Experience studio-grade audio with active hybrid noise cancellation, 40-hour battery life, ergonomic memory foam earcups, and crystal-clear microphone voice isolation.</p>
        <p>Equipped with Bluetooth 5.3 multipoint pairing, transparency audio passthrough, and custom equalizer presets via the mobile companion app.</p>
    </main>
</body>
</html>"""

@test_app.get("/page/param-variant", response_class=HTMLResponse)
def page_param_variant(sort: str = "default", ref: str = "none"):
    # Parameter variant has same content and correctly declares canonical to param-base
    return """<!DOCTYPE html>
<html>
<head>
    <title>Wireless Noise-Cancelling Headphones Pro</title>
    <link rel="canonical" href="http://127.0.0.1:8001/page/param-base" />
</head>
<body>
    <main>
        <h1>Wireless Noise-Cancelling Headphones Pro</h1>
        <p>Experience studio-grade audio with active hybrid noise cancellation, 40-hour battery life, ergonomic memory foam earcups, and crystal-clear microphone voice isolation.</p>
        <p>Equipped with Bluetooth 5.3 multipoint pairing, transparency audio passthrough, and custom equalizer presets via the mobile companion app.</p>
    </main>
</body>
</html>"""

@test_app.get("/page/redirect-start")
def page_redirect():
    return RedirectResponse(url="/page/redirect-destination", status_code=301)

@test_app.get("/page/redirect-destination", response_class=HTMLResponse)
def page_redirect_dest():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Redirect Destination Page</title>
</head>
<body>
    <article>
        <h1>Redirect Destination Page</h1>
        <p>This page was reached successfully following an HTTP 301 Permanent Redirect response.</p>
    </article>
</body>
</html>"""

@test_app.get("/page/http-404-broken")
def page_404():
    return Response(content="Page Not Found", status_code=404, media_type="text/plain")

@test_app.get("/page/http-500-error")
def page_500():
    return Response(content="Internal Server Error", status_code=500, media_type="text/plain")

@test_app.get("/page/blocked-by-robots", response_class=HTMLResponse)
def page_blocked_robots():
    return """<!DOCTYPE html>
<html>
<body><p>This page is disallowed in robots.txt.</p></body>
</html>"""
