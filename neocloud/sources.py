"""Bounded exact-URL retrieval. Sources are untrusted data, never instructions."""
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit, urljoin
import httpx
from bs4 import BeautifulSoup
from .catalog import SOURCES

ALLOWED_HOSTS = {"www.sec.gov", "investors.coreweave.com", "nebius.com", "iren.com",
                 "ir.iren.com", "ir.bitdeer.com"}


async def retrieve(url: str) -> dict:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS or parsed.port not in (None,443) or parsed.username:
        raise ValueError("Source URL outside primary-source allowlist")
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        async with client.stream("GET", url, headers={"User-Agent": os.getenv(
            "SEC_USER_AGENT", "NeoCloudResearch research@example.com")}) as response:
            if response.status_code != 200:
                return {"url": url, "status": "unavailable", "http_status": response.status_code}
            if not any(t in response.headers.get("content-type", "") for t in ("text/", "application/xhtml")):
                return {"url": url, "status": "unsupported_content_type"}
            data = bytearray()
            async for chunk in response.aiter_bytes():
                data.extend(chunk)
                if len(data) > 4_000_000:
                    return {"url": url, "status": "source_too_large"}
    soup = BeautifulSoup(bytes(data), "html.parser")
    for tag in soup(["script","style","noscript"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    # Scope long SEC filings to relevant financing passages instead of prompting entire documents.
    # Put note tables and hedge paragraphs ahead of incidental mentions in filing front matter.
    priority = list(re.finditer(r"note\s*10[. :–—-]*\s*debt|notes? payable|debt financing|interest rate swaps|hedging activities",text,re.I))
    matches = priority + list(re.finditer(r"debt|credit facility|convertible|hedg|swap|customer|agreement|senior notes", text, re.I))
    passages = []
    ranges = []
    for match in matches:
        start, end = max(0, match.start()-500), min(len(text), match.start()+2100)
        if any(start < b and end > a for a,b in ranges):
            continue
        passages.append(text[start:end])
        ranges.append((start,end))
        if sum(map(len,passages)) >= 22000:
            break
    links = []
    for anchor in soup.find_all("a",href=True):
        target = urljoin(url,anchor["href"]).split("#")[0]
        part = urlsplit(target)
        if part.scheme=="https" and part.hostname in ALLOWED_HOSTS and not part.username and part.port in (None,443) and target not in links:
            if re.search(r"debt|financ|senior|notes|filing|sec|2026|agreement|customer",target,re.I):
                links.append(target)
        if len(links)>=40:
            break
    return {"url":url, "status":"retrieved", "title":soup.title.get_text() if soup.title else parsed.hostname,
            "discovered_links":links,
            "retrieved_at":datetime.now(timezone.utc).isoformat(),
            "text":"\n[…]\n".join(passages) if passages else text[:22000],
            "scope_warning":"Scoped passages; absence is not proof of no debt."}


async def source_bundle(ticker: str, urls: list[str] | None = None):
    results = []
    for url in (urls or SOURCES[ticker])[:3]:
        try:
            results.append(await retrieve(url))
        except (httpx.HTTPError, ValueError):
            results.append({"url":url,"status":"retrieval_failed"})
    return results
