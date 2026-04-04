import ipaddress
import socket

import httpx


LOCAL_TARGETS = {"localhost", "127.0.0.1", "demo.vulnerable.local"}


def _normalize_value(value: str | None, fallback: str = "Unknown") -> str:
    cleaned = (value or "").strip()
    return cleaned or fallback


def _resolve_public_ip(target: str) -> str:
    cleaned = (target or "").strip()
    if not cleaned:
        return ""

    if cleaned in LOCAL_TARGETS:
        return "127.0.0.1"

    try:
        ip_obj = ipaddress.ip_address(cleaned)
        if ip_obj.is_private or ip_obj.is_loopback:
            return str(ip_obj)
        return str(ip_obj)
    except ValueError:
        pass

    try:
        resolved = socket.gethostbyname(cleaned)
        return resolved
    except OSError:
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
    resolved_ip = _resolve_public_ip(target)

    if target in LOCAL_TARGETS:
        return _local_network_payload("127.0.0.1")

    if resolved_ip:
        try:
            ip_obj = ipaddress.ip_address(resolved_ip)
            if ip_obj.is_private or ip_obj.is_loopback:
                return _local_network_payload(resolved_ip)
        except ValueError:
            pass

    lookup_target = resolved_ip or (target or "").strip()
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
        ) as client:
            for url, normalizer in providers:
                try:
                    resp = await client.get(url, timeout=6.0)
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
        print(f"Geolocation lookup failed: {exc}")

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
