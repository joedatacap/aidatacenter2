"""Bounded exact-URL retrieval. Sources are untrusted data, never instructions."""
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit, urljoin
import httpx
from bs4 import BeautifulSoup
from .catalog import SOURCES
from .connectivity import classify_error,http_policy_allows,policy_snapshot

ALLOWED_HOSTS = {"www.sec.gov", "investors.coreweave.com", "nebius.com", "iren.com",
                 "ir.iren.com", "ir.bitdeer.com"}


def scoped_passages(text):
    if len(text) <= 22000:
        return text
    # Actual note headings precede cross-references and generic financing mentions.
    # Include whole debt tables and their units rather than isolated row fragments.
    sections = list(re.finditer(r"\b\d+\.\s+Debt\s+(?:The total|As of|Debt obligations)", text, re.I))
    passages = []
    ranges = []
    for match in sections[:1]:
        start, end = match.start(), min(len(text), match.start()+14000)
        passages.append(text[start:end]); ranges.append((start,end))
    priority = list(re.finditer(r"interest rate swaps|hedging activities|notes? payable|debt financing", text, re.I))
    matches = priority + list(re.finditer(r"debt|credit facility|convertible|hedg|swap|customer|agreement|senior notes", text, re.I))
    for match in matches:
        start, end = max(0, match.start()-500), min(len(text), match.start()+2100)
        if any(start < b and end > a for a,b in ranges):
            continue
        remaining = 22000-sum(map(len,passages))
        if remaining <= 0:
            break
        end = min(end,start+remaining)
        passages.append(text[start:end]); ranges.append((start,end))
    return "\n[…]\n".join(passages) if passages else text[:22000]


async def retrieve(url: str) -> dict:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS or parsed.port not in (None,443) or parsed.username:
        raise ValueError("Source URL outside primary-source allowlist")
    original_url=url
    redirects=[]
    data=bytearray()
    try:
        async with httpx.AsyncClient(timeout=15,follow_redirects=False) as client:
            for _ in range(4):
                parsed=urlsplit(url)
                if parsed.scheme!='https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.port not in (None,443):
                    return {'url':original_url,'status':'unavailable','category':'unapproved_redirect','redirects':redirects}
                async with client.stream('GET',url,headers={'User-Agent':os.getenv('SEC_USER_AGENT','NeoCloudResearch research@example.com')}) as response:
                    if response.status_code in (301,302,303,307,308):
                        if not response.headers.get('location'):
                            break
                        url=urljoin(url,response.headers['location'])
                        redirects.append(url)
                        continue
                    if response.status_code!=200:
                        category={403:'http_403',404:'http_404',429:'http_429',401:'authentication_failure'}.get(response.status_code,'provider_http_error')
                        return {'url':original_url,'status':'unavailable','category':category,
                                'http_status':response.status_code,'final_url':url,'redirects':redirects}
                    if not any(t in response.headers.get('content-type','') for t in ('text/','application/xhtml')):
                        return {'url':original_url,'status':'unavailable','category':'unsupported_content_type'}
                    data=bytearray()
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data)>4_000_000:
                            return {'url':original_url,'status':'unavailable','category':'source_too_large'}
                    break
            else:
                return {'url':original_url,'status':'unavailable','category':'redirect_limit'}
            if not data:
                return {'url':original_url,'status':'unavailable','category':'empty_source'}
    except httpx.HTTPError as exc:
        category=classify_error(exc)
        if isinstance(exc,httpx.ProxyError) and http_policy_allows(parsed.hostname) is False:
            category='network_policy_restriction'
        return {'url':original_url,'status':'unavailable','category':category,'error_type':type(exc).__name__,
                'http_policy_allows_host':http_policy_allows(parsed.hostname)}
    soup = BeautifulSoup(bytes(data), "html.parser")
    for tag in soup(["script","style","noscript"]):
        tag.decompose()
    for tag in soup.find_all(lambda tag: tag.name.lower() in ('ix:hidden','ix:header')):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    # Scope long SEC filings to relevant financing passages instead of prompting entire documents.
    # Put note tables and hedge paragraphs ahead of incidental mentions in filing front matter.
    links = []
    for anchor in soup.find_all("a",href=True):
        target = urljoin(url,anchor["href"]).split("#")[0]
        part = urlsplit(target)
        if part.scheme=="https" and part.hostname in ALLOWED_HOSTS and not part.username and part.port in (None,443) and target not in links:
            if re.search(r"debt|financ|senior|notes|filing|sec|2026|agreement|customer",target,re.I):
                links.append(target)
        if len(links)>=40:
            break
    return {"url":original_url, "final_url":url, "redirects":redirects, "status":"retrieved", "title":soup.title.get_text() if soup.title else parsed.hostname,
            "discovered_links":links,
            "retrieved_at":datetime.now(timezone.utc).isoformat(),
            "text":scoped_passages(text),
            "scope_warning":"Scoped passages; absence is not proof of no debt."}


async def source_bundle(ticker,urls=None,cache=None,before_fetch=None,on_result=None):
    """Per-URL positive/negative memory survives task retries through the run snapshot."""
    cache=cache if cache is not None else {}
    for old in list(cache.values()):
        if isinstance(old,list):
            for source in old:
                if isinstance(source,dict) and source.get('url'):
                    cache.setdefault(source['url'],source)
    requested=list(dict.fromkeys(urls or SOURCES[ticker]))
    queue=requested+[u for u in SOURCES[ticker] if u not in requested]
    results=[];fetched=0
    fingerprint=hashlib.sha256(json.dumps(policy_snapshot(),sort_keys=True).encode()).hexdigest()
    for url in queue:
        if url not in requested and any(s['status']=='retrieved' for s in results):
            break
        host=urlsplit(url).hostname
        host_key='_blocked_host:'+str(host)
        cached=url in cache and isinstance(cache[url],dict)
        if cached:
            result=cache[url]
        elif cache.get(host_key,{}).get('policy_fingerprint')==fingerprint:
            result={'url':url,'status':'unavailable','category':'network_policy_restriction',
                    'skipped_known_host_failure':True}
            cache[url]=result;cached=True
        else:
            if fetched>=3:
                break
            if before_fetch:
                await before_fetch(url)
            try:
                result=await retrieve(url)
            except ValueError:
                result={'url':url,'status':'unavailable','category':'unapproved_source_url'}
            fetched+=1
            cache[url]=result
            if result.get('category')=='network_policy_restriction':
                cache[host_key]={'policy_fingerprint':fingerprint}
        results.append({**result,'cache_hit':cached})
        if on_result:
            await on_result(result,cached)
    return results
