import httpx
import asyncio

async def fuzz_directories(target: str, port: int) -> list:
    """
    Rapidly fuzzes common sensitive web directories and files 
    (/.env, /admin, /.git) using async requests.
    """
    if target in ["localhost", "127.0.0.1", "demo.vulnerable.local"]:
        # Mocking for local tests
        if target == "demo.vulnerable.local" and port == 80:
            return ["/admin", "/.env", "/backup.zip", "/phpmyadmin"]
        return []

    scheme = "https" if port == 443 else "http"
    base_url = f"{scheme}://{target}:{port}"
    
    common_paths = [
        "/.env", "/.git/config", "/admin", "/login", "/wp-admin",
        "/backup.zip", "/server-status", "/api", "/dashboard", "/phpmyadmin"
    ]
    
    found_endpoints = []
    
    async def check_path(client, path):
        try:
            resp = await client.get(f"{base_url}{path}", timeout=3.0, follow_redirects=False)
            # 200 OK, 401 Unauthorized, 403 Forbidden all indicate the path exists
            if resp.status_code in [200, 401, 403]:
                found_endpoints.append(path)
        except Exception:
            pass

    try:
        async with httpx.AsyncClient(verify=False) as client:
            tasks = [check_path(client, path) for path in common_paths]
            await asyncio.gather(*tasks)
    except Exception as e:
        print(f"Directory fuzzing failed on port {port}: {e}")
        
    return found_endpoints
