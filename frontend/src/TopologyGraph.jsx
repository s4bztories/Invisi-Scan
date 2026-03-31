import React, { useEffect, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

export default function TopologyGraph({ data }) {
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.clientWidth,
        height: 400
      });
    }
  }, []);

  useEffect(() => {
    if (!data) return;

    const nodes = [];
    const links = [];

    // Target root node
    nodes.push({ id: 'target', group: 1, label: data.target || "Target", val: 5 });

    // Subdomains mapping
    if (data.subdomains && data.subdomains.length > 0) {
        data.subdomains.forEach((sub, i) => {
            nodes.push({ id: `sub-${i}`, group: 2, label: sub, val: 3 });
            links.push({ source: 'target', target: `sub-${i}` });
        });
    }

    // IP node
    nodes.push({ id: 'ip', group: 3, label: data.geolocation?.ip || "Unknown IP", val: 4 });
    links.push({ source: 'target', target: 'ip' });

    // Open ports mapping from IP
    if (data.open_ports) {
        data.open_ports.forEach(port => {
            nodes.push({ id: `port-${port}`, group: 4, label: `Port ${port}`, val: 2 });
            links.push({ source: 'ip', target: `port-${port}` });
            
            // CVE mapping
            if (data.cves && data.cves[port]) {
                data.cves[port].forEach((cve, i) => {
                    nodes.push({ id: `cve-${port}-${i}`, group: 5, label: cve.id, val: 1 });
                    links.push({ source: `port-${port}`, target: `cve-${port}-${i}` });
                });
            }
        });
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setGraphData({ nodes, links });
  }, [data]);

  return (
    <div ref={containerRef} className="w-full h-[400px] border border-white/5 bg-black/40 rounded-xl overflow-hidden relative">
      <div className="absolute top-4 left-4 z-10 text-xs font-semibold text-slate-400 flex gap-4">
         <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-indigo-500"></span> Primary</span>
         <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-400"></span> Surface</span>
         <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400"></span> Service</span>
         <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400"></span> Vulns</span>
      </div>
      {dimensions.width > 0 && graphData.nodes.length > 0 && (
        <ForceGraph2D
          width={dimensions.width}
          height={dimensions.height}
          graphData={graphData}
          nodeLabel="label"
          nodeColor={node => {
            switch(node.group) {
              case 1: return '#6366f1'; // Indigo Root
              case 2: return '#60a5fa'; // Blue Subdomains
              case 3: return '#a855f7'; // Purple IP
              case 4: return '#34d399'; // Emerald Ports
              case 5: return '#f87171'; // Red CVEs
              default: return '#cbd5e1';
            }
          }}
          linkColor={() => 'rgba(255, 255, 255, 0.1)'}
          backgroundColor="transparent"
          d3VelocityDecay={0.8}
          warmupTicks={50}
        />
      )}
    </div>
  );
}
