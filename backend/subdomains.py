import httpx
import re

def is_domain(target: str) -> bool:
    # Basic check to see if target is a domain vs an IP
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", target):
        return False
    if target == "localhost":
        return False
    return True

async def enumerate_subdomains(domain: str) -> list:
    if not is_domain(domain):
        return []
        
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                subs = set()
                for entry in data:
                    name = entry.get("name_value", "")
                    if name:
                        for n in name.split('\n'):
                            n = n.strip()
                            if n.endswith(domain) and n != domain and '*' not in n:
                                subs.add(n)
                return sorted(list(subs))[:50] # cap at 50 to avoid overwhelming UI
    except Exception as e:
        print(f"Subdomain enumeration failed: {e}")
    return []
