import requests
from typing import Dict, List

class CVELookup:
    API_BASE = 'https://cve.circl.lu/api/search/'

    def _service_from_banner(self, banner: str) -> str:
        b = (banner or '').lower()
        if 'apache' in b:
            return 'apache'
        if 'nginx' in b:
            return 'nginx'
        if 'iis' in b or 'microsoft-iis' in b:
            return 'iis'
        if 'ssh' in b:
            return 'openssh'
        if 'mysql' in b or 'mariadb' in b:
            return 'mysql'
        if 'tomcat' in b:
            return 'tomcat'
        return ''

    def check_services(self, banners: Dict[int, str]) -> Dict[int, List[dict]]:
        results = {}
        for port, banner in banners.items():
            svc = self._service_from_banner(banner or '')
            results[port] = []
            if svc:
                try:
                    r = requests.get(self.API_BASE + svc, timeout=6)
                    if r.status_code == 200:
                        data = r.json()
                        results[port] = data[:5]
                except Exception:
                    results[port] = []
        return results
