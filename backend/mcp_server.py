import asyncio
import json
import sys
from typing import Dict, Any, List, Optional
from backend.core.scanner_async import AsyncPortScanner
from backend.core.cve_lookup import CVELookup
from backend.core.rag_engine import RAGEngine
from backend.core.ml_risk_scorer import MLRiskScorer
from backend import database


class InvisiScanMCPServer:
    """
    Standardized Model Context Protocol (MCP) Server for Invisi-Scan.
    Allows external AI models to discover and execute Invisi-Scan tools seamlessly.
    """

    TOOLS = [
        {
            "name": "invisi_port_scan",
            "description": "Scans network ports of a target domain or IP address and returns open services.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target hostname or IP address"},
                    "fast_mode": {"type": "boolean", "description": "True for standard top ports, False for 1-1024", "default": True}
                },
                "required": ["target"]
            }
        },
        {
            "name": "invisi_lookup_cve",
            "description": "Looks up known CVE security vulnerabilities for service banners.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "banners": {"type": "object", "description": "Dictionary mapping port numbers to service banner strings"}
                },
                "required": ["banners"]
            }
        },
        {
            "name": "invisi_query_rag",
            "description": "Queries the Invisi-Scan RAG knowledge base for security advisories and past scan histories.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Security question or target hostname to query"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "invisi_ml_risk_analysis",
            "description": "Calculates ML threat risk scores and attack surface metrics for a target.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "open_ports": {"type": "array", "items": {"type": "integer"}, "description": "List of open port numbers"},
                    "cves": {"type": "object", "description": "CVE lookup results per port"}
                },
                "required": ["open_ports"]
            }
        }
    ]

    def __init__(self):
        self.rag_engine = RAGEngine()
        self.ml_scorer = MLRiskScorer()
        self.cve_lookup = CVELookup()

    def get_manifest(self) -> Dict[str, Any]:
        return {
            "name": "Invisi-Scan SOC MCP Server",
            "version": "1.0.0",
            "description": "Model Context Protocol interface for network intelligence, port scanning, CVE lookup, and RAG knowledge.",
            "tools": self.TOOLS
        }

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "invisi_port_scan":
            target = arguments.get("target", "").strip()
            fast_mode = arguments.get("fast_mode", True)
            ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306, 3389, 8080] if fast_mode else list(range(1, 1025))
            scanner = AsyncPortScanner(target, ports, concurrency=50, timeout=2.5)
            open_ports = await scanner.run()
            return {"target": target, "open_ports": open_ports, "total_scanned": len(ports)}

        elif name == "invisi_lookup_cve":
            banners = arguments.get("banners", {})
            # Ensure keys are integers
            parsed_banners = {int(k): str(v) for k, v in banners.items()}
            cve_results = self.cve_lookup.check_services(parsed_banners)
            return {"cve_results": cve_results}

        elif name == "invisi_query_rag":
            query = arguments.get("query", "")
            results = self.rag_engine.search(query, top_k=3)
            return {"query": query, "results": results}

        elif name == "invisi_ml_risk_analysis":
            open_ports = arguments.get("open_ports", [])
            cves = arguments.get("cves", {})
            eval_result = self.ml_scorer.evaluate(open_ports, cves)
            return eval_result

        else:
            raise ValueError(f"Unknown MCP tool: {name}")


async def run_stdio_mcp_server():
    """Stdio JSON-RPC loop for MCP integration with external agent runners."""
    server = InvisiScanMCPServer()

    while True:
        try:
            line = await asyncio.to_thread(sys.stdin.readline)
            if not line:
                break
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")

            if method == "tools/list":
                res = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": server.TOOLS}}
            elif method == "tools/call":
                params = req.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = await server.execute_tool(tool_name, tool_args)
                res = {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
            else:
                res = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_res = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
            sys.stdout.write(json.dumps(err_res) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(run_stdio_mcp_server())
