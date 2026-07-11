"""
Public IP enrichment ("whatsmyip"-style reverse lookup) for the WAN IP tools.

Given public IPs already resolved by the WAN IP summaries, looks up
ISP/organisation, ASN, reverse DNS, and IP geolocation from an external
IP-intelligence provider and returns normalised records. Strictly additive:
failures degrade to warnings and per-IP error entries instead of raising, so
enrichment can never break the base WAN IP output.

Providers:
  - "ip-api"  (default, no key) — ip-api.com free batch endpoint. The free
    tier is HTTP-only and rate-limited (~15 batch requests/min); only the
    bare IP addresses are sent.
  - "ipinfo"  — ipinfo.io over HTTPS, one request per IP. Optional token
    (`ipinfo_token` in settings / SCM_MCP_IPINFO_TOKEN) raises rate limits.

Enrichment sends tenant public IPs to a third-party service, so it is
opt-in per tool call (`enrich=true`) and never runs by default. Results are
cached in-process for `_CACHE_TTL` so repeated report runs in one session
don't re-hit provider rate limits.
"""

from __future__ import annotations

import ipaddress
import time
from collections.abc import Iterable
from typing import Any

import requests

from .logging import get_logger

logger = get_logger(__name__)

_CACHE_TTL = 6 * 3600  # ISP/geo assignments rarely change
_cache: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}

_IP_API_FIELDS = "status,message,query,reverse,isp,org,as,asname,city,regionName,country,lat,lon"
_IP_API_BATCH_URL = "http://ip-api.com/batch"
_IPINFO_URL = "https://ipinfo.io/{ip}/json"
_TIMEOUT = (5, 15)


def global_ips(raw: Iterable[str]) -> list[str]:
    """Normalise candidate addresses to unique, globally-routable IPs.

    Accepts bare IPs or CIDR-suffixed interface addresses ("203.0.113.5/30").
    RFC1918/loopback/link-local/etc. are dropped — there is nothing an
    external provider can say about them. Order-preserving dedupe.
    """
    seen: list[str] = []
    for item in raw:
        candidate = str(item or "").strip().split("/")[0]
        if not candidate:
            continue
        try:
            addr = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if addr.is_global and str(addr) not in seen:
            seen.append(str(addr))
    return seen


def enrich_public_ips(
    ips: Iterable[str],
    provider: str = "",
    token: str = "",
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Look up ISP/ASN/rDNS/geo for each globally-routable IP.

    Returns ({ip: record}, warnings) and never raises. Records are
    normalised across providers:
      {ip, reverse_dns, isp, org, asn, as_name,
       city, region, country, latitude, longitude, source}

    provider/token default to the server settings (`ip_enrichment_provider`,
    `ipinfo_token`); provider falls back to "ip-api" if settings are
    unavailable.
    """
    targets = global_ips(ips)
    if not targets:
        return {}, []

    if not provider or (provider == "ipinfo" and not token):
        s_provider, s_token = _settings_provider()
        provider = provider or s_provider
        token = token or s_token

    now = time.time()
    results: dict[str, dict[str, Any]] = {}
    misses: list[str] = []
    for ip in targets:
        hit = _cache.get((provider, ip))
        if hit and now - hit[0] < _CACHE_TTL:
            results[ip] = hit[1]
        else:
            misses.append(ip)

    warnings: list[str] = []
    if misses:
        try:
            if provider == "ipinfo":
                fetched, warnings = _lookup_ipinfo(misses, token)
            elif provider == "ip-api":
                fetched, warnings = _lookup_ip_api(misses)
            else:
                return results, [f"unknown ip_enrichment_provider {provider!r}"]
        except Exception as exc:
            logger.debug("ip_enrichment_failed", provider=provider, error=str(exc))
            return results, [f"ip enrichment via {provider} failed: {exc}"]
        for ip, rec in fetched.items():
            _cache[(provider, ip)] = (now, rec)
            results[ip] = rec

    return results, warnings


def _settings_provider() -> tuple[str, str]:
    try:
        from ..config.settings import get_settings

        s = get_settings()
        return s.ip_enrichment_provider, s.ipinfo_token.get_secret_value()
    except Exception:
        return "ip-api", ""


def _lookup_ip_api(ips: list[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """ip-api.com batch lookup — up to 100 IPs per POST."""
    records: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    for start in range(0, len(ips), 100):
        chunk = ips[start : start + 100]
        resp = requests.post(
            _IP_API_BATCH_URL,
            params={"fields": _IP_API_FIELDS},
            json=chunk,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        for row in resp.json():
            ip = row.get("query", "")
            if row.get("status") != "success":
                warnings.append(f"{ip}: {row.get('message', 'lookup failed')}")
                continue
            records[ip] = {
                "ip": ip,
                "reverse_dns": row.get("reverse", ""),
                "isp": row.get("isp", ""),
                "org": row.get("org", ""),
                "asn": (row.get("as", "") or "").split(" ")[0],
                "as_name": row.get("asname", ""),
                "city": row.get("city", ""),
                "region": row.get("regionName", ""),
                "country": row.get("country", ""),
                "latitude": row.get("lat"),
                "longitude": row.get("lon"),
                "source": "ip-api.com",
            }
    return records, warnings


def _lookup_ipinfo(ips: list[str], token: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """ipinfo.io lookup — one HTTPS GET per IP; token optional."""
    records: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    for ip in ips:
        resp = requests.get(
            _IPINFO_URL.format(ip=ip),
            params={"token": token} if token else None,
            timeout=_TIMEOUT,
        )
        if resp.status_code != 200:
            warnings.append(f"{ip}: ipinfo.io HTTP {resp.status_code}")
            continue
        row = resp.json()
        # org arrives as "AS15169 Google LLC"; loc as "51.5074,-0.1278"
        org_raw = row.get("org", "") or ""
        asn, _, org_name = org_raw.partition(" ")
        if not asn.startswith("AS"):
            asn, org_name = "", org_raw
        lat: float | None = None
        lon: float | None = None
        loc = row.get("loc", "") or ""
        if "," in loc:
            try:
                lat_s, lon_s = loc.split(",", 1)
                lat, lon = float(lat_s), float(lon_s)
            except ValueError:
                pass
        records[ip] = {
            "ip": ip,
            "reverse_dns": row.get("hostname", ""),
            "isp": org_name,
            "org": org_name,
            "asn": asn,
            "as_name": org_name,
            "city": row.get("city", ""),
            "region": row.get("region", ""),
            "country": row.get("country", ""),
            "latitude": lat,
            "longitude": lon,
            "source": "ipinfo.io",
        }
    return records, warnings
