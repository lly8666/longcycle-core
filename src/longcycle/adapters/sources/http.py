from __future__ import annotations

import ipaddress
import socket
from collections.abc import AsyncIterator
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

from longcycle.domain.models import DiscoveryItem, RawPayload, SourceDefinition
from longcycle.ports.source import DiscoveryContext, FetchContext, SourceNotModified


def canonicalize_http_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("only absolute HTTP(S) URLs are supported")
    host = parsed.hostname.lower()
    default_port = (parsed.scheme.lower() == "http" and parsed.port == 80) or (parsed.scheme.lower() == "https" and parsed.port == 443)
    netloc = host if not parsed.port or default_port else f"{host}:{parsed.port}"
    path = parsed.path or "/"
    return urlunsplit((parsed.scheme.lower(), netloc, path, parsed.query, ""))


def _assert_public_host(url: str) -> None:
    parsed = urlsplit(url)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL is missing a hostname")
    if hostname.lower() in {"localhost", "localhost.localdomain"}:
        raise ValueError("local hosts are not allowed")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, parsed.port or 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise ValueError(f"hostname cannot be resolved: {hostname}") from exc
    if not addresses:
        raise ValueError(f"hostname has no routable addresses: {hostname}")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if any((ip.is_private, ip.is_loopback, ip.is_link_local, ip.is_multicast, ip.is_reserved, ip.is_unspecified)):
            raise ValueError(f"refusing non-public address for {hostname}")


class HttpDocumentSource:
    plugin_name = "http_document"

    def __init__(self, definition: SourceDefinition) -> None:
        self.definition = definition
        urls = definition.config.get("urls", [])
        if not isinstance(urls, list) or not all(isinstance(item, str) for item in urls):
            raise ValueError("http_document urls must be a list of strings")
        self.urls = tuple(canonicalize_http_url(item) for item in urls)
        allowed_domains = definition.config.get("allowed_domains", [])
        if not isinstance(allowed_domains, list):
            raise ValueError("allowed_domains must be a list")
        self.allowed_domains = {str(item).lower() for item in allowed_domains}
        self.user_agent = str(definition.config.get("user_agent", "LongcycleCollector/0.1"))

    def _assert_allowed(self, url: str) -> None:
        host = urlsplit(url).hostname or ""
        if self.allowed_domains and host.lower() not in self.allowed_domains:
            raise ValueError(f"domain is not allowlisted: {host}")
        _assert_public_host(url)

    async def discover(self, context: DiscoveryContext) -> AsyncIterator[DiscoveryItem]:
        del context
        for url in self.urls:
            yield DiscoveryItem(source_id=self.definition.id, url=url)

    async def fetch(self, item: DiscoveryItem, context: FetchContext) -> RawPayload:
        url = canonicalize_http_url(item.url)
        headers = {"User-Agent": self.user_agent, "Accept": "*/*", **context.conditional_headers}
        async with httpx.AsyncClient(
            timeout=context.timeout_seconds,
            follow_redirects=False,
            headers=headers,
            trust_env=False,
        ) as client:
            for _ in range(6):
                self._assert_allowed(url)
                async with client.stream("GET", url) as response:
                    response_headers = {key.lower(): value for key, value in response.headers.items()}
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location:
                            raise ValueError("redirect response has no Location header")
                        url = canonicalize_http_url(urljoin(url, location))
                        continue
                    if response.status_code == 304:
                        raise SourceNotModified(url, response_headers)
                    response.raise_for_status()
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > context.maximum_bytes:
                            raise ValueError(f"response exceeds {context.maximum_bytes} bytes")
                    content_type = response.headers.get("content-type", "application/octet-stream").split(";", 1)[0]
                    return RawPayload(
                        content=bytes(body),
                        content_type=content_type,
                        canonical_url=url,
                        status_code=response.status_code,
                        headers=response_headers,
                    )
        raise ValueError("too many redirects")
