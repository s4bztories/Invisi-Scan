import json
import math
import re
from typing import Dict, List, Any, Optional
from collections import Counter


class RAGEngine:
    """
    Lightweight, fast, self-contained Retrieval-Augmented Generation (RAG) Engine.
    Uses TF-IDF vector similarity over document chunks of historical scans, CVEs, and security guides.
    """

    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_vectors: List[Dict[str, float]] = []
        self._init_knowledge_base()

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r"\b\w+\b", text.lower())
        return [w for w in words if len(w) > 2]

    def _init_knowledge_base(self):
        """Seed initial security advisories and remediation guidelines into RAG memory."""
        knowledge_seed = [
            {
                "id": "kb_ssh_hardening",
                "title": "SSH Hardening Best Practices",
                "content": "Port 22 SSH should disable root login, enforce key-based authentication (PubkeyAuthentication yes), change default port, and set AllowUsers. Disable SSH v1 and weak ciphers like 3DES.",
                "category": "remediation"
            },
            {
                "id": "kb_ftp_security",
                "title": "FTP / Anonymous Login Risks",
                "content": "Port 21 FTP allows plain-text password transmission. If anonymous login is enabled, malicious actors can read/write files. Migrate to SFTP/SCP or enforce FTPS (TLS).",
                "category": "remediation"
            },
            {
                "id": "kb_http_waf",
                "title": "Web Application Firewall (WAF) and Headers",
                "content": "Enforce Strict-Transport-Security (HSTS), Content-Security-Policy (CSP), X-Frame-Options DENY, and X-Content-Type-Options nosniff. Deploy Cloudflare, ModSecurity, or AWS WAF to mitigate OWASP Top 10 vulnerabilities.",
                "category": "web"
            },
            {
                "id": "kb_smb_vuln",
                "title": "SMB Port 445 & MS17-010 EternalBlue",
                "content": "Port 445 SMB v1 is vulnerable to EternalBlue (MS17-010, CVE-2017-0144). Ensure SMB v1 is disabled, patch KB4012598, and block port 445 from public internet edge firewalls.",
                "category": "cve"
            },
            {
                "id": "kb_rdp_bluekeep",
                "title": "RDP Port 3389 & BlueKeep CVE-2019-0708",
                "content": "Port 3389 RDP without Network Level Authentication (NLA) is vulnerable to BlueKeep (CVE-2019-0708) remote code execution. Enforce NLA, require VPN access, and enable 2FA/MFA.",
                "category": "cve"
            },
            {
                "id": "kb_database_ports",
                "title": "Database Exposure (MySQL 3306, Postgres 5432, Redis 6379)",
                "content": "Database ports should never be exposed publicly to 0.0.0.0. Bind to 127.0.0.1 or use private VPC peering. Redis unauthenticated instances lead to remote root compromise via SSH keys.",
                "category": "database"
            }
        ]

        for doc in knowledge_seed:
            self.add_document(doc["id"], doc["title"], doc["content"], doc.get("category", "general"))

    def add_document(self, doc_id: str, title: str, content: str, category: str = "scan_report", metadata: Optional[dict] = None):
        full_text = f"{title} {content}"
        tokens = self._tokenize(full_text)
        doc = {
            "id": doc_id,
            "title": title,
            "content": content,
            "category": category,
            "tokens": tokens,
            "metadata": metadata or {}
        }
        self.documents.append(doc)
        self._rebuild_index()

    def index_scan_reports(self, scan_reports: List[dict]):
        """Index database scan reports into RAG memory dynamically."""
        for report in scan_reports:
            target = report.get("target", "unknown")
            risk = report.get("risk_level", "Unknown")
            open_ports = report.get("open_ports_count", 0)
            json_str = report.get("report_json", "{}")
            
            try:
                data = json.loads(json_str) if isinstance(json_str, str) else json_str
            except Exception:
                data = {}

            cves = data.get("cves", {})
            cve_summary = []
            for p, c_list in cves.items():
                for c in c_list[:3]:
                    cid = c.get("id") or c.get("cve") or ""
                    cvuln = c.get("vuln") or c.get("summary") or ""
                    if cid:
                        cve_summary.append(f"Port {p} {cid}: {cvuln}")

            content = f"Target {target} scanned. Risk Level: {risk}. Open Ports Count: {open_ports}. " + " ".join(cve_summary)
            self.add_document(
                doc_id=f"scan_{report.get('id', target)}",
                title=f"Scan Report for {target}",
                content=content,
                category="historical_scan",
                metadata={"target": target, "risk": risk, "open_ports": open_ports}
            )

    def _rebuild_index(self):
        num_docs = len(self.documents)
        if num_docs == 0:
            return

        doc_freq = Counter()
        for doc in self.documents:
            unique_tokens = set(doc["tokens"])
            for t in unique_tokens:
                doc_freq[t] += 1

        self.idf = {t: math.log((1 + num_docs) / (1 + freq)) + 1.0 for t, freq in doc_freq.items()}
        self.doc_vectors = []

        for doc in self.documents:
            tf = Counter(doc["tokens"])
            vec = {}
            norm = 0.0
            for t, count in tf.items():
                tfidf = (count / len(doc["tokens"])) * self.idf.get(t, 1.0)
                vec[t] = tfidf
                norm += tfidf * tfidf

            norm = math.sqrt(norm) or 1.0
            normalized_vec = {t: val / norm for t, val in vec.items()}
            self.doc_vectors.append(normalized_vec)

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not self.documents:
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return self.documents[:top_k]

        q_tf = Counter(q_tokens)
        q_vec = {}
        q_norm = 0.0
        for t, count in q_tf.items():
            tfidf = (count / len(q_tokens)) * self.idf.get(t, 1.0)
            q_vec[t] = tfidf
            q_norm += tfidf * tfidf

        q_norm = math.sqrt(q_norm) or 1.0
        q_vec = {t: val / q_norm for t, val in q_vec.items()}

        scores = []
        for idx, d_vec in enumerate(self.doc_vectors):
            score = sum(val * d_vec.get(t, 0.0) for t, val in q_vec.items())
            scores.append((score, self.documents[idx]))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scores if score > 0.01][:top_k] or self.documents[:top_k]
