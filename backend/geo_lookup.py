import ipaddress
import socket
import asyncio
import httpx

LOCAL_TARGETS = {
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "testclient",
    "demo.vulnerable.local",
}


def _normalize_value(value: str | None, fallback: str = "Unknown") -> str:
    cleaned = (value or "").strip()
    return cleaned or fallback


def _is_private_or_local_ip(ip_str: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
    except ValueError:
        return False


async def _resolve_public_ip_async(target: str) -> str:
    cleaned = (target or "").strip().lower()
    if not cleaned or cleaned in LOCAL_TARGETS:
        return "127.0.0.1"

    if _is_private_or_local_ip(cleaned):
        return cleaned

    try:
        loop = asyncio.get_running_loop()
        info = await loop.getaddrinfo(cleaned, None)
        if info:
            resolved_ip = info[0][4][0]
            return resolved_ip
    except Exception:
        pass

    return ""


def _local_network_payload(ip_address: str) -> dict:
    ip_value = ip_address or "127.0.0.1"
    return {
        "ip": ip_value,
        "country": "Local Network",
        "city": "Internal",
        "isp": "Private SOC Network",
        "org": "Invisi-Scan Administration",
        "asn": "AS00000 PRIVATE",
    }


def _normalize_ipwhois(data: dict, resolved_ip: str) -> dict:
    if not data.get("success", False):
        return {}

    return {
        "ip": _normalize_value(data.get("ip"), resolved_ip or "Unknown"),
        "country": _normalize_value(data.get("country")),
        "city": _normalize_value(data.get("city")),
        "isp": _normalize_value(data.get("connection", {}).get("isp")),
        "org": _normalize_value(data.get("connection", {}).get("org")),
        "asn": _normalize_value(data.get("connection", {}).get("asn")),
    }


def _normalize_ipapi(data: dict, resolved_ip: str) -> dict:
    if data.get("error"):
        return {}

    asn = _normalize_value(data.get("asn"))
    if asn != "Unknown" and not asn.startswith("AS"):
        asn = f"AS{asn}"

    return {
        "ip": _normalize_value(data.get("ip"), resolved_ip or "Unknown"),
        "country": _normalize_value(data.get("country_name") or data.get("country")),
        "city": _normalize_value(data.get("city") or data.get("region")),
        "isp": _normalize_value(data.get("org")),
        "org": _normalize_value(data.get("org")),
        "asn": asn,
    }


async def lookup_geo(target: str) -> dict:
    cleaned = (target or "").strip().lower()

    if not cleaned or cleaned in LOCAL_TARGETS or _is_private_or_local_ip(cleaned):
        return _local_network_payload(cleaned or "127.0.0.1")

    resolved_ip = await _resolve_public_ip_async(cleaned)

    if resolved_ip and _is_private_or_local_ip(resolved_ip):
        return _local_network_payload(resolved_ip)

    lookup_target = resolved_ip or cleaned
    if not lookup_target:
        return {}

    providers = [
        (f"https://ipwho.is/{lookup_target}", _normalize_ipwhois),
        (f"https://ipapi.co/{lookup_target}/json/", _normalize_ipapi),
    ]

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            headers={"User-Agent": "Invisi-Scan/1.0"},
            timeout=3.0,
        ) as client:
            for url, normalizer in providers:
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue
                    payload = normalizer(resp.json(), resolved_ip)
                    if payload and any(
                        payload.get(field) not in {"", "Unknown"}
                        for field in ("ip", "city", "country", "isp")
                    ):
                        return payload
                except Exception:
                    continue
    except Exception as exc:
        pass

    if resolved_ip:
        return {
            "ip": resolved_ip,
            "country": "Unknown",
            "city": "Unknown",
            "isp": "Unknown",
            "org": "Unknown",
            "asn": "Unknown",
        }

    return {}

