import httpx

async def detect_waf(target: str, port: int) -> str:
    """
    Attempts to identify Web Application Firewalls (Cloudflare, Akamai, AWS)
    by inspecting HTTP Response headers and cookies.
    """
    if target in ["localhost", "127.0.0.1", "demo.vulnerable.local"]:
        return "No WAF Detected"

    scheme = "https" if port == 443 else "http"
    url = f"{scheme}://{target}:{port}/"
    
    waf_signatures = {
        "cloudflare": "Cloudflare",
        "akamai": "Akamai",
        "sucuri": "Sucuri",
        "incapsula": "Imperva Incapsula",
        "awselb": "AWS WAF",
        "f5": "F5 BIG-IP"
    }
    
    try:
        async with httpx.AsyncClient(verify=False) as client:
            resp = await client.head(url, timeout=3.0, follow_redirects=True)
            server_header = resp.headers.get("Server", "").lower()
            
            for sig, name in waf_signatures.items():
                if sig in server_header:
                    return name
                    
            # Check cookies for typical WAF trackers
            cookies = str(resp.cookies).lower()
            if "__cfduid" in cookies or "cf_clearance" in cookies:
                return "Cloudflare"
                
    except Exception as e:
        print(f"WAF detection error on port {port}: {e}")
        
    return "No WAF Detected"
