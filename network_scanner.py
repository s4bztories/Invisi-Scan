# network_scanner.py
import platform
import subprocess
import ipaddress
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

def get_local_os():
    return platform.system().lower()

def ping_host(ip: str, timeout: int = 1000) -> bool:
    system = get_local_os()
    try:
        if system == "windows":
            res = subprocess.run(["ping", "-n", "1", "-w", str(timeout), str(ip)],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return res.returncode == 0
        else:
            timeout_secs = max(1, int(round(timeout / 1000)))
            res = subprocess.run(["ping", "-c", "1", "-W", str(timeout_secs), str(ip)],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return res.returncode == 0
    except Exception:
        return False

def parse_arp_table() -> Dict[str, str]:
    system = get_local_os()
    mapping = {}
    try:
        if system == "windows":
            out = subprocess.check_output(["arp", "-a"], stderr=subprocess.DEVNULL).decode(errors="ignore")
            for line in out.splitlines():
                m = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:-]{17})", line)
                if m:
                    ip = m.group(1)
                    mac = m.group(2).replace('-', ':').lower()
                    mapping[ip] = mac
        else:
            try:
                out = subprocess.check_output(["ip", "neigh"], stderr=subprocess.DEVNULL).decode(errors="ignore")
                for line in out.splitlines():
                    parts = line.split()
                    if len(parts) >= 5:
                        ip = parts[0]
                        if "lladdr" in parts:
                            idx = parts.index("lladdr")
                            mac = parts[idx+1].lower()
                            mapping[ip] = mac
            except Exception:
                out = subprocess.check_output(["arp", "-n"], stderr=subprocess.DEVNULL).decode(errors="ignore")
                for line in out.splitlines():
                    m = re.search(r"\((\d+\.\d+\.\d+\.\d+)\) at ([0-9a-fA-F:]{17})", line)
                    if m:
                        ip = m.group(1)
                        mac = m.group(2).lower()
                        mapping[ip] = mac
    except Exception:
        pass
    return mapping

def ip_range_from_cidr(cidr_or_ip: str) -> List[str]:
    try:
        if "/" in cidr_or_ip:
            net = ipaddress.ip_network(cidr_or_ip, strict=False)
            return [str(ip) for ip in net.hosts()]
        else:
            return [cidr_or_ip]
    except Exception:
        if "-" in cidr_or_ip:
            base, rng = cidr_or_ip.rsplit(".", 1)
            start_end = rng.split("-", 1)
            if len(start_end) == 2:
                start, end = int(start_end[0]), int(start_end[1])
                return [f"{base}.{i}" for i in range(start, end+1)]
        return []

def ping_sweep(ip_list: List[str], workers: int = 100, timeout_ms: int = 500) -> List[str]:
    active = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(ping_host, ip, timeout_ms): ip for ip in ip_list}
        for fut in as_completed(futures):
            ip = futures[fut]
            try:
                ok = fut.result()
                if ok:
                    active.append(ip)
            except Exception:
                pass
    return sorted(active, key=lambda x: tuple(int(p) for p in x.split('.')))

def discover_network(target_or_cidr: str, workers: int = 200, timeout_ms: int = 500) -> List[Dict[str, str]]:
    ips = ip_range_from_cidr(target_or_cidr)
    if not ips:
        return []
    active = ping_sweep(ips, workers=workers, timeout_ms=timeout_ms)
    arp = parse_arp_table()
    results = []
    for ip in active:
        results.append({
            "ip": ip,
            "mac": arp.get(ip, ""),
        })
    return results

if __name__ == "__main__":
    import argparse, json
    p = argparse.ArgumentParser(description="Network discovery (ping sweep + arp)")
    p.add_argument("--target", "-t", required=True, help="Target IP or CIDR (e.g. 192.168.1.0/24 or 192.168.1.5)")
    p.add_argument("--workers", type=int, default=200)
    p.add_argument("--timeout", type=int, default=500, help="ping timeout in ms (windows uses ms, linux converted)")
    args = p.parse_args()
    res = discover_network(args.target, workers=args.workers, timeout_ms=args.timeout)
    print(json.dumps(res, indent=2))
