import os
from typing import Dict, List

USE_OPENAI = bool(os.environ.get('OPENAI_API_KEY'))
if USE_OPENAI:
    try:
        import openai
        openai.api_key = os.environ.get('OPENAI_API_KEY')
    except Exception:
        USE_OPENAI = False

class AIHelper:
    def __init__(self, model: str = 'gpt-3.5-turbo'):
        self.model = model

    def _local_summary(self, items: List[dict]) -> str:
        if not items:
            return 'No CVE hits found by quick heuristic.'
        out = []
        for it in items:
            cid = it.get('id') or it.get('cve') or 'UNKNOWN'
            summary = it.get('summary') or it.get('vuln') or ''
            out.append(f"- {cid}: {summary[:250].strip()}")
        return '\n'.join(out)

    def explain_cves(self, cve_results: Dict[int, List[dict]]) -> Dict[int, str]:
        explanations = {}
        for port, items in cve_results.items():
            if not items:
                explanations[port] = 'No quick CVE hits found by heuristic.'
                continue
            if USE_OPENAI:
                try:
                    prompt = """You are an elite expert Penetration Tester.
For the following CVEs:
1. Provide a brief 1-sentence executive risk summary.
2. Provide an exact Metasploit (MSFConsole) command or Exploit-DB reference to test it.
3. Provide the exact bash command or methodology to remediate/patch the vulnerability.
Format your response in ultra-concise, highly readable Markdown.\n\nCVEs:\n"""
                    for it in items:
                        cid = it.get('id') or it.get('cve') or 'UNKNOWN'
                        summary = it.get('summary') or it.get('vuln') or ''
                        prompt += f"{cid}: {summary}\n\n"
                    resp = openai.ChatCompletion.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=500,
                        temperature=0.2,
                    )
                    text = resp['choices'][0]['message']['content'].strip()
                    explanations[port] = text
                    continue
                except Exception as e:
                    explanations[port] = f"(AI lookup failed) {str(e)}\n\n" + self._local_summary(items)
                    continue
            explanations[port] = self._local_summary(items)
        return explanations
