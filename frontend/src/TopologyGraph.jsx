import React, { useMemo } from 'react';

const NODE_COLORS = {
  target: '#818cf8',
  subdomain: '#60a5fa',
  ip: '#a78bfa',
  port: '#34d399',
  cve: '#f87171',
};

const WIDTH = 1200;
const HEIGHT = 420;

function truncate(label, max = 22) {
  if (!label) return '';
  return label.length > max ? `${label.slice(0, max - 1)}…` : label;
}

export default function TopologyGraph({ data }) {
  const { nodes, links } = useMemo(() => {
    if (!data) return { nodes: [], links: [] };

    const items = [];
    const edges = [];

    const targetNode = { id: 'target', type: 'target', label: data.target || 'Target', x: 140, y: HEIGHT / 2 };
    items.push(targetNode);

    const ipNode = { id: 'ip', type: 'ip', label: data.geolocation?.ip || 'Unknown IP', x: 420, y: HEIGHT / 2 };
    items.push(ipNode);
    edges.push({ from: 'target', to: 'ip' });

    const subdomains = (data.subdomains || []).slice(0, 10);
    subdomains.forEach((sub, i) => {
      const spacing = HEIGHT / (subdomains.length + 1);
      const node = {
        id: `sub-${i}`,
        type: 'subdomain',
        label: sub,
        x: 420,
        y: spacing * (i + 1),
      };
      items.push(node);
      edges.push({ from: 'target', to: node.id });
    });

    const ports = (data.open_ports || []).slice(0, 14);
    ports.forEach((port, i) => {
      const spacing = HEIGHT / (ports.length + 1);
      const portNode = {
        id: `port-${port}`,
        type: 'port',
        label: `Port ${port}`,
        x: 700,
        y: spacing * (i + 1),
      };
      items.push(portNode);
      edges.push({ from: 'ip', to: portNode.id });

      const cves = (data.cves?.[port] || []).slice(0, 2);
      cves.forEach((cve, idx) => {
        const cveNode = {
          id: `cve-${port}-${idx}`,
          type: 'cve',
          label: cve.id || 'CVE',
          x: 980,
          y: Math.max(26, Math.min(HEIGHT - 26, portNode.y + (idx === 0 ? -16 : 16))),
        };
        items.push(cveNode);
        edges.push({ from: portNode.id, to: cveNode.id });
      });
    });

    return { nodes: items, links: edges };
  }, [data]);

  const byId = useMemo(() => {
    const map = new Map();
    nodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [nodes]);

  if (nodes.length === 0) {
    return <div className="surface-card p-10 text-center text-slate-400">No topology data available yet.</div>;
  }

  return (
    <div className="surface-card p-4 overflow-x-auto">
      <div className="flex flex-wrap gap-4 text-xs text-slate-400 mb-3 px-1">
        <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-indigo-400" /> Target</span>
        <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-purple-400" /> IP</span>
        <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-blue-400" /> Surface</span>
        <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-emerald-400" /> Ports</span>
        <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-rose-400" /> CVEs</span>
      </div>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full min-w-[860px] h-[390px]">
        {links.map((edge) => {
          const from = byId.get(edge.from);
          const to = byId.get(edge.to);
          if (!from || !to) return null;
          return (
            <line
              key={`${edge.from}-${edge.to}`}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke="rgba(148,163,184,0.25)"
              strokeWidth="1.5"
            />
          );
        })}
        {nodes.map((node) => (
          <g key={node.id}>
            <circle cx={node.x} cy={node.y} r={node.type === 'target' || node.type === 'ip' ? 8 : 6} fill={NODE_COLORS[node.type]} />
            <text x={node.x + 10} y={node.y + 4} fill="#cbd5e1" fontSize="12" fontFamily="ui-sans-serif, system-ui">
              {truncate(node.label)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
