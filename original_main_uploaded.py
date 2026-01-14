#!/usr/bin/env python3
import argparse
import asyncio
from rich.console import Console

from scanner_async import AsyncPortScanner
from banner import BannerGrabber
from cve_lookup import CVELookup
from ai_helper import AIHelper
from reporter import Reporter

console = Console()


# --------------------
# Parse port formats
# --------------------
def parse_ports(ports_str: str):
    ports = set()
    parts = ports_str.split(',')
    for p in parts:
        p = p.strip()
        if "-" in p:
            a, b = p.split('-')
            ports.update(range(int(a), int(b) + 1))
        else:
            ports.add(int(p))
    return sorted(ports)


# --------------------
# Scan Function
# --------------------
async def run_scan(target, ports, concurrency, timeout, savefile):
    console.rule(f"[green]Scanning {target}[/green]")

    scanner = AsyncPortScanner(target, ports, concurrency, timeout)
    open_ports = await scanner.run()
    console.print("[bold cyan]Open ports:[/bold cyan]", open_ports)

    grabber = BannerGrabber(target, timeout)
    banners = await grabber.grab_many(open_ports)

    cve = CVELookup()
    cve_results = cve.check_services(banners)

    ai = AIHelper()
    explanations = ai.explain_cves(cve_results)

    report = Reporter(target, open_ports, banners, cve_results, explanations)
    report.save(savefile)

    console.print(f"[bold green]Saved report → {savefile}[/bold green]")


# --------------------
# Main
# --------------------
def main():
    parser = argparse.ArgumentParser(description="AI Ethical Hacking Lab")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # --------------------
    # Scan Command
    # --------------------
    s = sub.add_parser("scan", help="Run port scan")
    s.add_argument("--target", "-t", required=True)
    s.add_argument("--ports", "-p", default="1-1024")
    s.add_argument("--concurrency", type=int, default=500)
    s.add_argument("--timeout", type=float, default=1.0)
    s.add_argument("--fast", action="store_true")
    s.add_argument("--save", default="report.json")

    # --------------------
    # Discover Command
    # --------------------
    d = sub.add_parser("discover", help="Discover devices in network")
    d.add_argument("--target", "-t", required=True,
                   help="Example: 192.168.1.0/24")

    args = parser.parse_args()

    # Handle discover
    if args.cmd == "discover":
        from network_scanner import discover
        console.rule(f"[cyan]Discovering {args.target}[/cyan]")
        devices = discover(args.target)
        console.print(f"[green]Active devices:[/green] {devices}")

        # Save output
        import json
        with open("discovery.json", "w") as f:
            json.dump({"network": args.target, "devices": devices}, f, indent=2)

        console.print("[bold green]Saved discovery.json[/bold green]")
        return

    # Handle scan
    if args.cmd == "scan":
        ports = (
            [21, 22, 80, 443, 3306, 8080]
            if args.fast
            else parse_ports(args.ports)
        )
        asyncio.run(run_scan(args.target, ports,
                             args.concurrency, args.timeout, args.save))


if __name__ == "__main__":
    main()
