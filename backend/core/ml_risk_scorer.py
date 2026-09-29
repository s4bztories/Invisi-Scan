import math
from typing import Dict, List, Any


class MLRiskScorer:
    """
    ML & Heuristic Threat Surface Engine.
    Calculates composite Risk Score (0-100), Attack Vector Surface Index,
    Exploit Likelihood, and Threat Category Breakdown for scan targets.
    """

    PORT_WEIGHTS = {
        21: {"name": "FTP", "weight": 7.5, "vector": "Plaintext Credentials / Anon Login"},
        22: {"name": "SSH", "weight": 5.0, "vector": "Brute-force / Key Compromise"},
        23: {"name": "Telnet", "weight": 9.0, "vector": "Unencrypted Administrative Protocol"},
        25: {"name": "SMTP", "weight": 4.0, "vector": "Open Relay / Mail Spoofing"},
        53: {"name": "DNS", "weight": 4.5, "vector": "Zone Transfer / Amplification DDOS"},
        80: {"name": "HTTP", "weight": 3.0, "vector": "Web Application Vectors"},
        110: {"name": "POP3", "weight": 4.0, "vector": "Unencrypted Mail Retrieval"},
        135: {"name": "RPC", "weight": 8.0, "vector": "Remote Procedure Call RCE"},
        139: {"name": "NetBIOS", "weight": 7.5, "vector": "SMB / NetBIOS Enumeration"},
        143: {"name": "IMAP", "weight": 4.0, "vector": "Unencrypted Mail Access"},
        443: {"name": "HTTPS", "weight": 2.0, "vector": "Encrypted Web Services"},
        445: {"name": "SMB", "weight": 9.5, "vector": "Critical EternalBlue / MSF Exploitation"},
        1433: {"name": "MSSQL", "weight": 8.5, "vector": "Database Injection / SA Compromise"},
        3306: {"name": "MySQL", "weight": 8.0, "vector": "Unauthenticated DB Access / SQLi"},
        3389: {"name": "RDP", "weight": 9.0, "vector": "BlueKeep RCE / Windows Desktop Hijack"},
        5432: {"name": "PostgreSQL", "weight": 8.0, "vector": "Database Privilege Escalation"},
        6379: {"name": "Redis", "weight": 9.5, "vector": "Unauthenticated Memory RCE / Root SSH Key Injection"},
        8080: {"name": "HTTP-Alt", "weight": 5.0, "vector": "Admin Portal Exposure"},
        27017: {"name": "MongoDB", "weight": 9.0, "vector": "Unauthenticated NoSQL Database"}
    }

    def evaluate(self, open_ports: List[int], cve_results: Dict[int, List[dict]], web_recon: Dict[str, dict] = None) -> Dict[str, Any]:
        web_recon = web_recon or {}
        
        base_score = 0.0
        vectors = []
        cve_count = 0
        critical_cve_count = 0

        # Calculate port risk weights
        for p in open_ports:
            info = self.PORT_WEIGHTS.get(p, {"name": f"Port {p}", "weight": 3.5, "vector": "Unknown Custom Service"})
            base_score += info["weight"]
            vectors.append({"port": p, "service": info["name"], "risk_factor": info["weight"], "threat_vector": info["vector"]})

        # Calculate CVE severity additions
        for port, cves in cve_results.items():
            for c in cves:
                cve_count += 1
                cid = c.get("id") or c.get("cve") or ""
                summary = (c.get("summary") or c.get("vuln") or "").lower()
                
                if "critical" in summary or "remote code execution" in summary or "rce" in summary or "ms17-010" in summary:
                    critical_cve_count += 1
                    base_score += 15.0
                else:
                    base_score += 5.0

        # Check WAF presence
        waf_detected = False
        for p_str, w_info in web_recon.items():
            waf = w_info.get("waf", "")
            if waf and waf != "No WAF Detected":
                waf_detected = True

        if waf_detected:
            base_score = max(0.0, base_score - 10.0)  # WAF mitigation reduces composite threat level

        # Normalize score to 0-100 scale using logarithmic sigmoid curve
        scaled_score = min(100.0, round((100.0 / (1.0 + math.exp(-0.08 * (base_score - 20)))), 1))
        if not open_ports:
            scaled_score = 0.0

        # Categorize threat tier
        if scaled_score >= 75.0 or critical_cve_count > 0:
            threat_level = "CRITICAL"
        elif scaled_score >= 50.0:
            threat_level = "HIGH"
        elif scaled_score >= 25.0:
            threat_level = "MEDIUM"
        else:
            threat_level = "LOW"

        return {
            "risk_score": scaled_score,
            "threat_level": threat_level,
            "total_open_ports": len(open_ports),
            "total_cves": cve_count,
            "critical_cves": critical_cve_count,
            "waf_protected": waf_detected,
            "threat_vectors": vectors,
            "attack_surface_index": round(min(10.0, len(open_ports) * 0.8 + cve_count * 1.2), 1),
            "recommendation": self._get_recommendation(threat_level, critical_cve_count, waf_detected)
        }

    def _get_recommendation(self, level: str, critical_cves: int, waf: bool) -> str:
        if level == "CRITICAL":
            return "IMMEDIATE ACTION REQUIRED: Critical remote code execution vectors identified. Quarantine target IP, close unneeded ports (445/3389/6379), and apply patch bulletins immediately."
        elif level == "HIGH":
            return "HIGH RISK: Exposing administrative and database services to public networks. Implement strict firewall rules and turn on TOTP/2FA."
        elif level == "MEDIUM":
            return "MEDIUM RISK: Standard web and network ports active. Ensure software versions are updated and configure Web Application Firewall (WAF)."
        return "LOW RISK: Target perimeter appears baseline hardened. Perform periodic autopilot monitoring."
