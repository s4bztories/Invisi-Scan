import os
import json
from typing import Dict, List, Any, Optional
from backend.core.rag_engine import RAGEngine

def _call_openai(messages: List[dict], model: str = "gpt-3.5-turbo", max_tokens: int = 700) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except (ImportError, AttributeError):
        import openai
        openai.api_key = api_key
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return resp["choices"][0]["message"]["content"].strip()


class AIChatbot:
    """
    SOC AI Assistant Chatbot with RAG Integration.
    Answers security analyst questions, suggests Metasploit payloads, analyzes scan reports,
    and pulls historical audit context from RAGEngine.
    """

    def __init__(self, rag_engine: Optional[RAGEngine] = None, model: str = "gpt-3.5-turbo"):
        self.rag_engine = rag_engine or RAGEngine()
        self.model = model

    def chat(self, user_query: str, history: Optional[List[dict]] = None, current_report: Optional[dict] = None) -> Dict[str, Any]:
        """
        Process a user question with RAG context retrieval and return structured AI response.
        """
        user_query_clean = (user_query or "").strip()
        if not user_query_clean:
            return {"answer": "Please ask a question about network security, scan reports, or CVE mitigations.", "rag_sources": []}

        # Retrieve relevant RAG context
        rag_results = self.rag_engine.search(user_query_clean, top_k=3)
        context_chunks = []
        sources = []

        for doc in rag_results:
            context_chunks.append(f"[{doc['title']}]\n{doc['content']}")
            sources.append({"title": doc["title"], "id": doc["id"], "category": doc["category"]})

        context_str = "\n\n".join(context_chunks)

        report_summary = ""
        if current_report:
            target = current_report.get("target", "Target")
            ports = current_report.get("open_ports", [])
            cves = current_report.get("cves", {})
            report_summary = f"\nACTIVE SCAN REPORT FOR {target}:\n- Open Ports: {ports}\n- CVEs Found: {json.dumps(cves)[:500]}\n"

        if os.environ.get("OPENAI_API_KEY"):
            try:
                system_prompt = (
                    "You are 'InvisiBot', an elite SOC Cyber Security AI Analyst & Penetration Testing Expert. "
                    "Use the provided RAG knowledge context and active scan report to answer user queries with precise, "
                    "actionable security insights, Metasploit commands, and remediation steps. Format with markdown."
                )

                user_prompt = f"RAG CONTEXT:\n{context_str}\n{report_summary}\n\nUSER QUESTION:\n{user_query_clean}"

                messages = [{"role": "system", "content": system_prompt}]
                if history:
                    for msg in history[-6:]:  # Keep recent conversation context
                        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

                messages.append({"role": "user", "content": user_prompt})

                answer = _call_openai(messages, model=self.model, max_tokens=700)
                return {"answer": answer, "rag_sources": sources}
            except Exception as e:
                pass

        # Smart Heuristic SOC Assistant Engine (Offline Mode / Local Fallback)
        answer = self._generate_heuristic_response(user_query_clean, context_str, current_report)
        return {"answer": answer, "rag_sources": sources}

    def _generate_heuristic_response(self, query: str, context_str: str, current_report: Optional[dict]) -> str:
        q = query.lower()

        if "metasploit" in q or "exploit" in q or "msfconsole" in q:
            return (
                "### ⚔️ Metasploit & Exploit Recommendations\n\n"
                "Here are target exploit vectors based on current intelligence:\n\n"
                "1. **Port 445 (SMB / MS17-010):**\n"
                "   ```bash\n"
                "   msfconsole -x 'use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS <target>; run'\n"
                "   ```\n"
                "2. **Port 21 (FTP Anonymous / Backdoor):**\n"
                "   ```bash\n"
                "   msfconsole -x 'use auxiliary/scanner/ftp/ftp_login; set RHOSTS <target>; run'\n"
                "   ```\n"
                "3. **Port 80/443 (Web Vulnerabilities / Directory Fuzzing):**\n"
                "   ```bash\n"
                "   gobuster dir -u http://<target> -w /usr/share/wordlists/dirb/common.txt\n"
                "   ```\n\n"
                "💡 **RAG Intelligence:** " + (context_str[:250] if context_str else "No target-specific CVE matches found.")
            )

        if "fix" in q or "remediate" in q or "patch" in q or "secure" in q:
            return (
                "### 🛡️ SOC Security Remediation Plan\n\n"
                "Based on Invisi-Scan threat intelligence guidelines:\n\n"
                "1. **Network Layer:** Filter sensitive administrative ports (`21`, `22`, `445`, `3306`, `3389`) using firewall rules (`iptables` / UFW / Cloud Security Groups).\n"
                "2. **Authentication:** Enforce multi-factor TOTP 2FA authentication for all user roles and disable anonymous FTP / unauthenticated database access.\n"
                "3. **Web Security:** Deploy WAF headers (`HSTS`, `CSP`, `X-Frame-Options DENY`) and place public services behind Cloudflare / reverse proxy.\n\n"
                "📌 **Knowledge Context:**\n" + (context_str if context_str else "No additional custom advisories recorded.")
            )

        if "scan" in q or "history" in q or "report" in q or "status" in q:
            if current_report:
                target = current_report.get("target", "Target")
                ports = current_report.get("open_ports", [])
                return (
                    f"### 📊 Active Target Summary for `{target}`\n\n"
                    f"- **Open Ports Identified:** `{ports}`\n"
                    f"- **Vulnerability Severity:** `{current_report.get('risk_level', 'Medium')}`\n"
                    f"- **Subdomains Discovered:** `{len(current_report.get('subdomains', []))}`\n\n"
                    "Use `/api/ai/chat` or ask me specific questions regarding port exploits or patch steps!"
                )
            return (
                "### 🔍 Invisi-Scan System Knowledge Search\n\n"
                "I searched the RAG Knowledge Base and found these relevant security insights:\n\n"
                f"{context_str[:600]}\n\n"
                "Ask me any specific security question or request Metasploit payload advice!"
            )

        # General Security Q&A Response
        return (
            "### 🤖 InvisiBot SOC Assistant\n\n"
            f"**Query:** *{query}*\n\n"
            "I have analyzed your request against the **Invisi-Scan Knowledge Base** and historical threat context:\n\n"
            f"{context_str[:500]}\n\n"
            "💡 **Recommended Next Actions:**\n"
            "- Run an OSINT subdomain scan on your target.\n"
            "- Check `/api/analytics` for cluster-wide exposure risks.\n"
            "- Ask me: *'Give me Metasploit commands for open ports'* or *'How to remediate SMB vulnerabilities'*."
        )
