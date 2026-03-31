import httpx
import re

async def lookup_geo(target: str) -> dict:
    # If it's a localhost or private IP, return dummy immediately
    if target in ["localhost", "127.0.0.1", "demo.vulnerable.local"]:
        return {
            "ip": "127.0.0.1",
            "country": "Local Network",
            "city": "Internal",
            "isp": "Private SOC Network",
            "org": "Invisi-Scan Administration",
            "asn": "AS00000 PRIVATE"
        }

    url = f"http://ip-api.com/json/{target}?fields=status,message,country,city,isp,org,as,query"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    return {
                        "ip": data.get("query", ""),
                        "country": data.get("country", ""),
                        "city": data.get("city", ""),
                        "isp": data.get("isp", ""),
                        "org": data.get("org", ""),
                        "asn": data.get("as", "")
                    }
    except Exception as e:
        print(f"Geolocation lookup failed: {e}")
        
    return {}
