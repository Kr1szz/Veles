"""Bounded, same-origin HTML crawler for user-supplied public company websites."""

import asyncio
import ipaddress
import socket
from collections import deque
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx

USER_AGENT = "VelesShieldDemoCrawler/1.0 (+respect robots.txt; bounded crawl)"
MAX_RESPONSE_BYTES = 1_000_000
REQUEST_DELAY_SECONDS = 0.25
REQUEST_TIMEOUT_SECONDS = 8.0


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.canonical = ""
        self.headings: list[str] = []
        self.links: list[str] = []
        self.text: list[str] = []
        self._title_depth = 0
        self._heading_depth = 0
        self._in_body = False
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attrs_map = dict(attrs)
        if tag == "title":
            self._title_depth += 1
        if tag == "body":
            self._in_body = True
        if tag in {"script", "style", "noscript", "svg", "template"}:
            self._ignored_depth += 1
        if tag in {"h1", "h2", "h3"}:
            self._heading_depth += 1
            self.headings.append("")
        if tag == "meta" and attrs_map.get("name", "").lower() == "description":
            self.description = attrs_map.get("content") or ""
        if tag == "link" and "canonical" in (attrs_map.get("rel") or "").lower().split():
            self.canonical = attrs_map.get("href") or ""
        if tag == "a" and attrs_map.get("href"):
            self.links.append(attrs_map["href"])

    def handle_endtag(self, tag: str):
        if tag == "title" and self._title_depth:
            self._title_depth -= 1
        if tag in {"h1", "h2", "h3"} and self._heading_depth:
            self._heading_depth -= 1
        if tag == "body":
            self._in_body = False
        if tag in {"script", "style", "noscript", "svg", "template"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str):
        clean = " ".join(data.split())
        if not clean:
            return
        if self._title_depth:
            self.title = f"{self.title} {clean}".strip()
        if self._heading_depth and self.headings:
            self.headings[-1] = f"{self.headings[-1]} {clean}".strip()
        if self._in_body and not self._ignored_depth:
            self.text.append(clean)


def _origin(url: str) -> str:
    parts = urlsplit(url)
    try:
        port = parts.port or (443 if parts.scheme.lower() == "https" else 80)
    except ValueError as exc:
        raise ValueError("Website URL contains an invalid port.") from exc
    hostname = parts.hostname.lower()
    if ":" in hostname:
        hostname = f"[{hostname}]"
    return f"{parts.scheme.lower()}://{hostname}:{port}"


def _normalize_url(url: str) -> str:
    url, _fragment = urldefrag(url)
    parts = urlsplit(url)
    path = parts.path or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def _internal_links(current_url: str, hrefs: list[str], origin: str) -> list[str]:
    links = []
    for href in hrefs:
        absolute = urljoin(current_url, href)
        parts = urlsplit(absolute)
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            continue
        try:
            if _origin(absolute) == origin:
                links.append(_normalize_url(absolute))
        except ValueError:
            continue
    return list(dict.fromkeys(links))[:100]


async def _validate_public_url(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("Enter a valid http or https website URL.")
    if parts.username or parts.password:
        raise ValueError("Website URLs must not include credentials.")
    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("Website URL contains an invalid port.") from exc
    if port and port not in {80, 443}:
        raise ValueError("Only standard HTTP and HTTPS ports are allowed.")

    host = parts.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise ValueError("Local and private network hosts cannot be crawled.")
    try:
        direct_ip = ipaddress.ip_address(host)
        addresses = [direct_ip]
    except ValueError:
        try:
            resolved = await asyncio.to_thread(socket.getaddrinfo, host, None, type=socket.SOCK_STREAM)
            addresses = [ipaddress.ip_address(item[4][0]) for item in resolved]
        except (OSError, ValueError) as exc:
            raise ValueError("Website host could not be resolved to a public address.") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("Local and private network addresses cannot be crawled.")


async def _read_response(client: httpx.AsyncClient, url: str) -> tuple[int, str, bytes, str | None]:
    async with client.stream("GET", url, headers={"User-Agent": USER_AGENT}) as response:
        if 300 <= response.status_code < 400:
            return response.status_code, str(response.url), b"", response.headers.get("location")
        content_type = response.headers.get("content-type", "")
        body = bytearray()
        async for chunk in response.aiter_bytes():
            body.extend(chunk)
            if len(body) > MAX_RESPONSE_BYTES:
                raise ValueError("HTML response exceeded the 1 MB page limit.")
        return response.status_code, str(response.url), bytes(body), content_type


async def _fetch_page(client: httpx.AsyncClient, url: str, origin: str):
    current = url
    for _ in range(4):
        await _validate_public_url(current)
        if _origin(current) != origin:
            raise ValueError("Redirect left the original website; crawl stopped at this URL.")
        status, final_url, body, content_type = await _read_response(client, current)
        if 300 <= status < 400:
            target = content_type
            if not target:
                raise ValueError("Website returned a redirect without a target.")
            current = urljoin(current, target)
            continue
        if status >= 400:
            return status, current, None, []
        if "text/html" not in content_type.lower():
            return status, current, None, []
        charset = "utf-8"
        for part in content_type.split(";")[1:]:
            if part.strip().lower().startswith("charset="):
                charset = part.split("=", 1)[1].strip(' "')
        try:
            html = body.decode(charset, errors="replace")
        except LookupError:
            html = body.decode("utf-8", errors="replace")
        parser = PageParser()
        parser.feed(html)
        links = _internal_links(current, parser.links, origin)
        return status, current, {
            "canonical_url": urljoin(current, parser.canonical) if parser.canonical else None,
            "title": parser.title[:512],
            "description": parser.description[:2000],
            "headings": [heading[:300] for heading in parser.headings if heading][:20],
            "links": links,
            "text_excerpt": " ".join(parser.text)[:1200],
        }, links
    raise ValueError("Website exceeded the redirect limit.")


async def crawl_site(start_url: str, max_pages: int) -> dict[str, Any]:
    start_url = _normalize_url(start_url.strip())
    await _validate_public_url(start_url)
    origin = _origin(start_url)
    start_url = urlunsplit((urlsplit(start_url).scheme, urlsplit(start_url).netloc, urlsplit(start_url).path or "/", urlsplit(start_url).query, ""))
    timeout = httpx.Timeout(REQUEST_TIMEOUT_SECONDS, connect=REQUEST_TIMEOUT_SECONDS)
    limits = httpx.Limits(max_connections=1, max_keepalive_connections=1)
    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=False, trust_env=False) as client:
        robots_url = f"{origin}/robots.txt"
        robots = RobotFileParser(robots_url)
        try:
            status, _url, body, _content_type = await _read_response(client, robots_url)
            if status == 404:
                robots.parse([])
            elif 200 <= status < 300:
                robots.parse(body.decode("utf-8", errors="replace").splitlines())
            else:
                robots.parse(["User-agent: *", "Disallow: /"])
        except Exception:
            robots.parse(["User-agent: *", "Disallow: /"])

        queue = deque([(start_url, 0)])
        visited: set[str] = set()
        discovered_urls: set[str] = {start_url}
        pages: list[dict[str, Any]] = []
        failed = 0
        robots_skipped = 0
        while queue and len(visited) < max_pages:
            url, depth = queue.popleft()
            if url in visited:
                continue
            visited.add(url)
            if _origin(url) != origin:
                continue
            if not robots.can_fetch(USER_AGENT, url):
                robots_skipped += 1
                continue
            if pages:
                await asyncio.sleep(REQUEST_DELAY_SECONDS)
            try:
                status, final_url, parsed, links = await _fetch_page(client, url, origin)
                page = {"url": final_url, "http_status": status, **(parsed or {})}
                if parsed is None:
                    page.update({"canonical_url": None, "title": "", "description": "", "headings": [], "links": [], "text_excerpt": ""})
                pages.append(page)
                if status >= 400:
                    page["error"] = f"HTTP {status}"
                    failed += 1
                elif parsed:
                    for link in links:
                        discovered_urls.add(link)
                        if link not in visited and depth < 2:
                            queue.append((link, depth + 1))
            except Exception as exc:
                pages.append({
                    "url": url, "http_status": None, "canonical_url": None, "title": "",
                    "description": "", "headings": [], "links": [], "text_excerpt": "",
                    "error": str(exc)[:512],
                })
                failed += 1

        return {
            "requested_url": start_url,
            "origin": origin,
            "status": "COMPLETED_WITH_ERRORS" if failed else "COMPLETED",
            "pages_discovered": len(discovered_urls),
            "pages_crawled": len(pages) - failed,
            "pages_failed": failed,
            "pages_skipped_robots": robots_skipped,
            "pages": pages,
        }
