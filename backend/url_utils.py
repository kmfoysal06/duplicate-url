import re
import socket
import ipaddress
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, urljoin
from typing import Tuple, Optional, Set

# List of common tracking/analytics query parameters that usually do NOT alter page content
TRACKING_PARAMS: Set[str] = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'gclid', 'fbclid', 'msclkid', 'mc_cid', 'mc_eid', '_ga', '_gl',
    'ref', 'source', 'trk', 's_kwcid'
}

# Blocked IP networks for SSRF protection
BLOCKED_NETWORKS = [
    ipaddress.ip_network('127.0.0.0/8'),        # IPv4 loopback
    ipaddress.ip_network('10.0.0.0/8'),         # RFC 1918 Class A
    ipaddress.ip_network('172.16.0.0/12'),      # RFC 1918 Class B
    ipaddress.ip_network('192.168.0.0/16'),     # RFC 1918 Class C
    ipaddress.ip_network('169.254.0.0/16'),     # Link-local / AWS metadata
    ipaddress.ip_network('0.0.0.0/8'),          # Current network
    ipaddress.ip_network('224.0.0.0/4'),        # Multicast
    ipaddress.ip_network('240.0.0.0/4'),        # Reserved
    ipaddress.ip_network('::1/128'),            # IPv6 loopback
    ipaddress.ip_network('fc00::/7'),           # IPv6 Unique Local
    ipaddress.ip_network('fe80::/10'),          # IPv6 Link-Local
]

def is_safe_url(url: str, allow_local_for_testing: bool = False) -> Tuple[bool, str]:
    """
    Validates a URL against Server-Side Request Forgery (SSRF).
    Blocks private IPs, link-local addresses, loopback, and cloud metadata endpoints.
    Allows localhost only when allow_local_for_testing is True (used for local test suites).
    """
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme.lower() not in ('http', 'https'):
            return False, f"Unsupported scheme '{parsed.scheme}'. Only http and https are allowed."
        
        hostname = parsed.hostname
        if not hostname:
            return False, "Invalid URL: missing hostname."

        # Reject obvious loopback names unless explicitly testing
        if not allow_local_for_testing:
            if hostname.lower() in ('localhost', '127.0.0.1', '::1', '0.0.0.0'):
                return False, "Security restriction: Requests to localhost are prohibited to protect internal services."
            
            # Resolve DNS to examine actual IP address
            try:
                addr_info = socket.getaddrinfo(hostname, None)
            except socket.gaierror as e:
                return False, f"DNS resolution failed for hostname '{hostname}': {str(e)}"
            
            for family, _, _, _, sockaddr in addr_info:
                ip_str = sockaddr[0]
                ip_obj = ipaddress.ip_address(ip_str)
                for net in BLOCKED_NETWORKS:
                    if ip_obj in net:
                        return False, f"Security restriction: Target IP {ip_str} belongs to private/internal network {net}."
                if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                    return False, f"Security restriction: Target IP {ip_str} is reserved or non-routable."

        return True, "URL is safe"
    except Exception as e:
        return False, f"URL validation error: {str(e)}"

def normalize_url(url: str, strip_tracking_params: bool = True) -> str:
    """
    Normalizes a URL for comparison while preserving content-altering query parameters.
    - Lowers scheme and domain
    - Removes default ports (80 for http, 443 for https)
    - Strips URL fragments (#anchor)
    - Normalizes path slashes (trailing slash standard, removes double slashes)
    - Sorts query parameters for deterministic comparison
    - Strips purely tracking parameters (utm_*, gclid) if requested, but preserves
      page/filter/sort/id query parameters that impact rendered content.
    """
    raw = url.strip()
    if not raw:
        return ""
    
    # Auto-prepend scheme if missing
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', raw):
        raw = 'https://' + raw

    parsed = urlparse(raw)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Strip default ports
    if scheme == 'http' and netloc.endswith(':80'):
        netloc = netloc[:-3]
    elif scheme == 'https' and netloc.endswith(':443'):
        netloc = netloc[:-4]

    # Normalize path: collapse multi-slashes
    path = parsed.path or '/'
    path = re.sub(r'/+', '/', path)

    # Process query parameters
    query = ""
    if parsed.query:
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        filtered_pairs = []
        for k, v in pairs:
            if strip_tracking_params and k.lower() in TRACKING_PARAMS:
                continue
            filtered_pairs.append((k, v))
        # Sort query parameters for consistent comparison
        filtered_pairs.sort(key=lambda x: (x[0], x[1]))
        if filtered_pairs:
            query = urlencode(filtered_pairs)

    # Reconstruct normalized URL without fragment
    normalized = urlunparse((scheme, netloc, path, '', query, ''))
    return normalized

def resolve_url(base_url: str, link: Optional[str]) -> Optional[str]:
    """
    Resolves relative links (like canonical tags) against the page's final URL.
    """
    if not link:
        return None
    link = link.strip()
    if not link:
        return None
    try:
        resolved = urljoin(base_url, link)
        return normalize_url(resolved, strip_tracking_params=False)
    except Exception:
        return link
