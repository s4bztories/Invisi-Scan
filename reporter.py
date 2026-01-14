import json
from datetime import datetime
from typing import Dict, List
import os

class Reporter:
    def __init__(self, target: str, open_ports: List[int], banners: Dict[int, str], cves: Dict[int, List[dict]], explanations: Dict[int, str]):
        self.target = target
        self.open_ports = open_ports
        self.banners = banners
        self.cves = cves
        self.explanations = explanations

    def _make_data(self):
        return {
            'target': self.target,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'open_ports': self.open_ports,
            'banners': self.banners,
            'cves': self.cves,
            'explanations': self.explanations,
        }

    def save(self, filename: str = 'report.json'):
        data = self._make_data()
        if filename.lower().endswith('.json'):
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        elif filename.lower().endswith('.md'):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# Scan report for {self.target}\n\n")
                f.write(f"Timestamp: {data['timestamp']}\n\n")
                f.write('## Open ports\n')
                for p in self.open_ports:
                    f.write(f"- {p}\n")
                f.write('\n## Banners\n')
                for p, b in self.banners.items():
                    f.write(f"### Port {p}\n```\n{b}\n```\n")
                f.write('\n## CVE Hints & Explanations\n')
                for p, expl in self.explanations.items():
                    f.write(f"### Port {p}\n{expl}\n\n")
        elif filename.lower().endswith('.html'):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"<html><head><meta charset='utf-8'><title>Scan report {self.target}</title></head><body>")
                f.write(f"<h1>Scan report for {self.target}</h1>")
                f.write(f"<p>Timestamp: {data['timestamp']}</p>")
                f.write("<h2>Open ports</h2><ul>")
                for p in self.open_ports:
                    f.write(f"<li>{p}</li>")
                f.write("</ul>")
                f.write("<h2>Banners</h2>")
                for p, b in self.banners.items():
                    f.write(f"<h3>Port {p}</h3><pre>{(b or '')}</pre>")
                f.write("<h2>CVE Hints & Explanations</h2>")
                for p, expl in self.explanations.items():
                    f.write(f"<h3>Port {p}</h3><pre>{(expl or '')}</pre>")
                f.write("</body></html>")
        else:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        try:
            base_dir = os.path.dirname(os.path.abspath(filename))
        except Exception:
            base_dir = os.getcwd()
        visual_path = os.path.join(base_dir, "report_visual.json")
        try:
            with open(visual_path, 'w', encoding='utf-8') as vf:
                json.dump(data, vf, indent=2)
        except Exception:
            pass
