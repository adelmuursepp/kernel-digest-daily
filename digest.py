"""
Kernel Fusion & CuTe DSL — Daily Research Digest

Queries arXiv and Semantic Scholar for recent papers on kernel fusion,
CuTe DSL, CUTLASS, and automated kernel writing. Sends a formatted
HTML email digest via Gmail API.
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ── Configuration ──────────────────────────────────────────────────────────────

RECIPIENT = os.environ.get("RECIPIENT_EMAIL", "adel.muursepp@gmail.com")

ARXIV_QUERIES = [
    'all:"kernel fusion" AND (GPU OR CUDA OR tensor)',
    'all:"CuTe" AND (CUTLASS OR NVIDIA OR kernel)',
    'all:"automated kernel" AND (GPU OR CUDA OR generation)',
    'all:"kernel compilation" AND (GPU OR tensor OR fusion)',
    'all:CUTLASS AND (fusion OR optimization OR automat*)',
    'all:"triton" AND ("kernel fusion" OR "code generation")',
    'all:"tensor compiler" AND (fusion OR GPU OR autotuning)',
]

SEMANTIC_SCHOLAR_QUERIES = [
    "CuTe DSL CUTLASS kernel fusion GPU",
    "automated kernel generation CUDA LLM",
    "kernel fusion compiler GPU optimization 2025",
    "tensor compiler autotuning GPU kernels",
]

LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "3"))


# ── arXiv Search ───────────────────────────────────────────────────────────────

def search_arxiv(query: str, max_results: int = 15) -> list[dict]:
    """Search arXiv API and return parsed entries."""
    params = urllib.parse.urlencode({
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    url = f"http://export.arxiv.org/api/query?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KernelDigest/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read().decode("utf-8")
    except Exception as e:
        print(f"  arXiv request failed for query: {e}", file=sys.stderr)
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(data)
    results = []
    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
        published = entry.find("atom:published", ns).text[:10]
        link = entry.find("atom:id", ns).text.strip()
        authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
        categories = [c.get("term") for c in entry.findall("atom:category", ns)]
        results.append({
            "title": title,
            "summary": summary[:500],
            "published": published,
            "url": link,
            "authors": authors[:5],
            "source": "arXiv",
            "categories": categories,
        })
    return results


# ── Semantic Scholar Search ────────────────────────────────────────────────────

def search_semantic_scholar(query: str, max_results: int = 10) -> list[dict]:
    """Search Semantic Scholar API."""
    params = urllib.parse.urlencode({
        "query": query,
        "limit": max_results,
        "fields": "title,abstract,url,year,authors,publicationDate,venue",
        "year": f"2025-2026",
    })
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KernelDigest/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  Semantic Scholar request failed: {e}", file=sys.stderr)
        return []

    results = []
    for paper in data.get("data", []):
        if not paper.get("title"):
            continue
        results.append({
            "title": paper["title"],
            "summary": (paper.get("abstract") or "")[:500],
            "published": paper.get("publicationDate", paper.get("year", "unknown")),
            "url": paper.get("url", ""),
            "authors": [a.get("name", "") for a in (paper.get("authors") or [])[:5]],
            "source": "Semantic Scholar",
            "venue": paper.get("venue", ""),
        })
    return results


# ── Deduplication & Filtering ──────────────────────────────────────────────────

def deduplicate(papers: list[dict]) -> list[dict]:
    """Remove duplicates based on normalized title."""
    seen = set()
    unique = []
    for p in papers:
        key = p["title"].lower().strip()[:80]
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def filter_recent(papers: list[dict], days: int) -> list[dict]:
    """Keep only papers published within the lookback window."""
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    recent = []
    for p in papers:
        pub = str(p.get("published", ""))[:10]
        if pub >= cutoff or pub == "unknown":
            recent.append(p)
    return recent


def relevance_score(paper: dict) -> int:
    """Simple keyword relevance scoring."""
    text = (paper.get("title", "") + " " + paper.get("summary", "")).lower()
    keywords = [
        "cute", "cutlass", "kernel fusion", "automated kernel", "kernel generation",
        "gpu kernel", "tensor compiler", "triton", "tma", "wgmma", "hopper",
        "blackwell", "flash attention", "cuda", "llm kernel", "agentic",
    ]
    return sum(1 for kw in keywords if kw in text)


# ── Email Formatting ───────────────────────────────────────────────────────────

def format_html(papers: list[dict], date_str: str) -> str:
    """Build the HTML email body."""
    if not papers:
        return f"""
        <html><body style="font-family: Arial, sans-serif; color: #333;">
        <h1>Kernel Fusion Research Digest — {date_str}</h1>
        <p>No new papers found in the last {LOOKBACK_DAYS} days. This can happen on
        slower weeks — the next digest will catch any new publications.</p>
        </body></html>
        """

    rows = ""
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p["authors"][:3])
        if len(p["authors"]) > 3:
            authors += " et al."
        venue = f' — <em>{p["venue"]}</em>' if p.get("venue") else ""
        summary = p["summary"][:300]
        if len(p["summary"]) > 300:
            summary += "…"
        rows += f"""
        <tr style="border-bottom: 1px solid #eee;">
            <td style="padding: 16px 0;">
                <h3 style="margin: 0 0 4px 0;">
                    <a href="{p['url']}" style="color: #1a1a2e; text-decoration: none;">{p['title']}</a>
                </h3>
                <p style="margin: 2px 0; color: #666; font-size: 13px;">
                    {authors}{venue} · {p['published']} · <span style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{p['source']}</span>
                </p>
                <p style="margin: 8px 0 0 0; font-size: 14px; color: #444;">{summary}</p>
            </td>
        </tr>
        """

    return f"""
    <html><body style="font-family: Arial, sans-serif; color: #222; max-width: 700px; margin: 0 auto;">
    <h1 style="color: #1a1a2e; border-bottom: 2px solid #e94560; padding-bottom: 8px;">
        Kernel Fusion & CuTe DSL — Research Digest
    </h1>
    <p style="color: #666;">{date_str} · {len(papers)} papers · Last {LOOKBACK_DAYS} days</p>

    <table style="width: 100%; border-collapse: collapse;">
        {rows}
    </table>

    <hr style="border: 1px solid #eee; margin: 24px 0;">
    <p style="color: #999; font-size: 12px;">
        Sources: arXiv, Semantic Scholar · Auto-generated daily via GitHub Actions
    </p>
    </body></html>
    """


# ── Gmail Send ─────────────────────────────────────────────────────────────────

def send_gmail(subject: str, html_body: str):
    """Send email via Gmail API using OAuth refresh token."""
    client_id = os.environ["GMAIL_CLIENT_ID"]
    client_secret = os.environ["GMAIL_CLIENT_SECRET"]
    refresh_token = os.environ["GMAIL_REFRESH_TOKEN"]

    # Exchange refresh token for access token
    token_data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()
    token_req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=token_data,
        method="POST",
    )
    with urllib.request.urlopen(token_req) as resp:
        access_token = json.loads(resp.read())["access_token"]

    # Build MIME message
    msg = MIMEMultipart("alternative")
    msg["To"] = RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    send_req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=json.dumps({"raw": raw}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(send_req) as resp:
        result = json.loads(resp.read())
        print(f"✓ Email sent. Message ID: {result['id']}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"Kernel Digest — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Lookback: {LOOKBACK_DAYS} days | Recipient: {RECIPIENT}\n")

    # Collect papers from all sources
    all_papers = []

    print("Searching arXiv...")
    for q in ARXIV_QUERIES:
        papers = search_arxiv(q)
        print(f"  '{q[:50]}...' → {len(papers)} results")
        all_papers.extend(papers)

    print("\nSearching Semantic Scholar...")
    for q in SEMANTIC_SCHOLAR_QUERIES:
        papers = search_semantic_scholar(q)
        print(f"  '{q}' → {len(papers)} results")
        all_papers.extend(papers)

    print(f"\nTotal raw results: {len(all_papers)}")

    # Deduplicate
    all_papers = deduplicate(all_papers)
    print(f"After dedup: {len(all_papers)}")

    # Filter recent
    recent = filter_recent(all_papers, LOOKBACK_DAYS)
    print(f"After recency filter ({LOOKBACK_DAYS}d): {len(recent)}")

    # If no recent papers, relax to all papers but cap at top 15
    if not recent:
        print("No papers in lookback window, using top results by relevance...")
        recent = all_papers

    # Score and sort
    for p in recent:
        p["_score"] = relevance_score(p)
    recent.sort(key=lambda p: p["_score"], reverse=True)

    # Take top 15
    top = recent[:15]
    print(f"Top papers for digest: {len(top)}\n")

    for p in top:
        print(f"  [{p['_score']}] {p['title'][:80]}  ({p['published']})")

    # Format and send
    date_str = datetime.utcnow().strftime("%B %d, %Y")
    subject = f"Kernel Fusion & CuTe DSL Research Digest — {date_str}"
    html = format_html(top, date_str)

    if os.environ.get("DRY_RUN"):
        print("\n[DRY RUN] Would send email. Saving HTML to digest_preview.html")
        with open("digest_preview.html", "w") as f:
            f.write(html)
    else:
        print("\nSending email...")
        send_gmail(subject, html)

    print("\nDone.")


if __name__ == "__main__":
    main()
