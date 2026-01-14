#!/usr/bin/env python3
import argparse
import asyncio
import ipaddress
import json
from urllib.parse import urlparse
from rich.console import Console
from scanner_async import AsyncPortScanner
from banner import BannerGrabber
from cve_lookup import CVELookup
from ai_helper import AIHelper
from reporter import Reporter

console = Console()

def normalize_target(raw: str) -> str:
    """Convert URL or input to hostname/IP"""
    raw = (raw or "").strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        try:
            p = urlparse(raw)
            return p.hostname
        except Exception:
            return raw
    # remove possible trailing slashes
    return raw.split("/")[0]

def parse_ports(ports_str: str):
    ports = set()
    try:
        parts = [p.strip() for p in ports_str.split(",") if p.strip()]
        for p in parts:
            if "-" in p:
                a, b = p.split("-", 1)
                ports.update(range(int(a), int(b) + 1))
            else:
                ports.add(int(p))
    except Exception:
        # fallback to common ports
        return [21,22,80,443,3306,8080]
    return sorted(ports)

async def run_scan(target, ports, concurrency, timeout, savefile):
    console.rule(f"[green]Scanning {target}[/green]")
    try:
        scanner = AsyncPortScanner(target, ports, concurrency, timeout)
        open_ports = await scanner.run()
    except Exception as e:
        console.print(f"[red]Scanner error:[/red] {e}")
        open_ports = []

    console.print("[bold cyan]Open ports:[/bold cyan]", open_ports)

    grabber = BannerGrabber(target, timeout)
    try:
        banners = await grabber.grab_many(open_ports)
    except Exception:
        banners = {}

    cve = CVELookup()
    try:
        cve_results = cve.check_services(banners)
    except Exception:
        cve_results = {}

    ai = AIHelper()
    explanations = ai.explain_cves(cve_results)

    report = Reporter(target, open_ports, banners, cve_results, explanations)
    report.save(savefile)

    console.print(f"[bold green]Saved report → {savefile}[/bold green]")


def main():
    parser = argparse.ArgumentParser(description="AI Ethical Hacking Lab - Upgraded")
    sub = parser.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="Run port scan")
    s.add_argument("--target", "-t", required=True)
    s.add_argument("--ports", "-p", default="1-1024")
    s.add_argument("--concurrency", type=int, default=500)
    s.add_argument("--timeout", type=float, default=1.0)
    s.add_argument("--fast", action="store_true")
    s.add_argument("--save", default="report.json")

    d = sub.add_parser("discover", help="Discover devices in network")
    d.add_argument("--target", "-t", required=True, help="Example: 192.168.1.0/24")

    args = parser.parse_args()

    if args.cmd == "discover":
        from network_scanner import discover_network
        console.rule(f"[cyan]Discovering {args.target}[/cyan]")
        devices = discover_network(args.target)
        console.print(f"[green]Active devices:[/green] {devices}")
        with open("discovery.json", "w") as f:
            json.dump({"network": args.target, "devices": devices}, f, indent=2)
        console.print("[bold green]Saved discovery.json[/bold green]")
        return

    if args.cmd == "scan":
        target = normalize_target(args.target)
        # validate IP or hostname
        try:
            # if a CIDR or IP accidentally passed, ensure we error early
            _ = ipaddress.ip_address(target)
        except Exception:
            pass
        ports = [21,22,80,443,3306,8080] if args.fast else parse_ports(args.ports)
        asyncio.run(run_scan(target, ports, args.concurrency, args.timeout, args.save))


if __name__ == "__main__":
    main()
