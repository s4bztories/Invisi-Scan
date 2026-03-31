import asyncio
from reporter import Reporter
from backend import database

async def run_demo_simulation(websocket, target: str, token: str):
    """
    Safely simulates a heavily vulnerable target to demonstrate 
    the SIEM/SOC dashboard in a full highly-critical threat state 
    for HR and Portfolio reviewers.
    """
    await websocket.send_json({"type": "info", "message": "🚨 CYBER RANGE SIMULATION ACTIVATED. 🚨"})
    await asyncio.sleep(1)
    
    # OSINT Subdomains
    await websocket.send_json({"type": "info", "message": "Performing OSINT Reconnaissance (Subdomains)..."})
    await asyncio.sleep(1)
    subs = ["dev.demo.local", "vpn.demo.local", "staging.demo.local", "admin.demo.local", "api.demo.local"]
    await websocket.send_json({"type": "info", "message": f"Found {len(subs)} subdomains."})
    await websocket.send_json({"type": "subdomains", "data": subs})
    await asyncio.sleep(1)
    
    # Ports
    ports = [21, 22, 80, 445]
    await websocket.send_json({"type": "info", "message": f"Starting port scan on {target} ({1024} ports)..."})
    for p in ports:
        await asyncio.sleep(0.8)
        await websocket.send_json({"type": "port_found", "port": p})
        
    await asyncio.sleep(1)
    
    # Banners
    await websocket.send_json({"type": "info", "message": "Executing deep service enumeration and banner grabbing..."})
    banners_data = {
        21: "vsftpd 2.3.4",
        22: "OpenSSH 4.7p1 Debian 8ubuntu1",
        80: "Apache httpd 2.4.49",
        445: "Samba smbd 3.X - 4.X (workgroup: WORKGROUP)"
    }
    await asyncio.sleep(2)
    await websocket.send_json({"type": "banners", "data": banners_data})
    
    # CVEs
    await websocket.send_json({"type": "info", "message": "Cross-referencing services with National Vulnerability Database (NVD)..."})
    await asyncio.sleep(2.5)
    cves_data = {
        21: [
            {"id": "CVE-2011-2523", "summary": "vsftpd 2.3.4 downloaded from the master site contains a malicious backdoor that executes arbitrary python code.", "score": 10.0}
        ],
        22: [],
        80: [
            {"id": "CVE-2021-41773", "summary": "A flaw was found in a change made to path normalization in Apache HTTP Server 2.4.49. An attacker could use a path traversal attack to map URLs to root folders.", "score": 7.5}
        ],
        445: [
            {"id": "CVE-2017-7494", "summary": "Samba is prone to a remote code execution vulnerability (SambaCry) allowing a malicious client to upload a shared library to a writable share.", "score": 9.8}
        ]
    }
    await websocket.send_json({"type": "cves", "data": cves_data})
    
    # AI Risk
    await websocket.send_json({"type": "info", "message": "Awaiting AI Threat Assessment Engine output..."})
    await asyncio.sleep(3)
    explanations = {
        21: "CRITICAL ALERT: The detected vsftpd 2.3.4 contains a highly infamous backdoor. Any attacker connecting to this port with a specific smiley-face username can spawn a reverse root shell, leading to immediate system takeover.",
        22: "Standard SSH port. While no critical CVEs were found for this specific version, ensure password authentication is strictly disabled and strong RSA keys are actively rotated.",
        80: "HIGH RISK: Apache 2.4.49 is notoriously vulnerable to a Path Traversal attack. Attackers can arbitrarily read files (like /etc/passwd) and potentially execute remote code via CGI.",
        445: "CRITICAL ALERT: SambaCry (CVE-2017-7494) allows an unauthenticated attacker to upload an executable and silently run it as root. Immediate patching is absolutely mandatory to prevent widespread ransomware lateral movement."
    }
    await websocket.send_json({"type": "explanations", "data": explanations})
    
    # Finalize Database Save
    await asyncio.sleep(1)
    await websocket.send_json({"type": "info", "message": "Generating executive summary report..."})
    report = Reporter(target, ports, banners_data, cves_data, explanations)
    report_data = report._make_data()
    report_data["subdomains"] = subs
    
    operator_role = "admin" if token == "ethical_scan_token_2026" else "guest"
    database.save_report(target, operator_role, report_data, risk_level="High")
    
    await websocket.send_json({"type": "complete", "report": report_data})
    await websocket.close()
