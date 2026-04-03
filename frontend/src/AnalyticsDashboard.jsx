import React, { useMemo, useState, useEffect } from 'react';
import { Activity, ShieldAlert, Target, Database } from 'lucide-react';

function buildDonutGradient(distribution) {
  const total = distribution.reduce((sum, d) => sum + d.value, 0) || 1;
  let cursor = 0;
  const segments = distribution
    .filter((d) => d.value > 0)
    .map((d) => {
      const start = cursor;
      cursor += (d.value / total) * 100;
      const color = d.name === 'High' ? '#ef4444' : d.name === 'Medium' ? '#f59e0b' : '#10b981';
      return `${color} ${start}% ${cursor}%`;
    });
  return `conic-gradient(${segments.join(', ')})`;
}

export default function AnalyticsDashboard({ authData }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/analytics`, {
      headers: { 'Authorization': `Bearer ${authData.token}` }
    })
      .then(r => r.json())
      .then(d => {
        if (d.ok) setData(d.analytics);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [authData.token]);

  const riskDistribution = useMemo(() => data?.risk_distribution || [], [data]);
  const timeline = useMemo(() => (data?.timeline || []).slice(-14), [data]);
  const maxScans = useMemo(() => Math.max(1, ...timeline.map((t) => t.scans || 0)), [timeline]);
  const donutGradient = useMemo(() => buildDonutGradient(riskDistribution), [riskDistribution]);

  if (loading) return <div className="text-white text-center py-20 animate-pulse">Initializing Global Uplink...</div>;
  if (!data) return <div className="text-red-400 text-center py-20">Failed to establish connection to Command Center.</div>;

  return (
    <div className="space-y-6 pb-12 w-full">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="surface-card p-6 flex flex-col items-center justify-center">
          <Database className="w-8 h-8 text-indigo-400 mb-2" />
          <p className="text-5xl font-bold text-white tabular-nums tracking-tight">{data.total_scans}</p>
          <p className="text-xs text-slate-400 mt-2 uppercase tracking-widest font-semibold">Total Scans Performed</p>
        </div>
        <div className="surface-card p-6 flex flex-col items-center justify-center">
          <ShieldAlert className="w-8 h-8 text-red-500 mb-2 drop-shadow-[0_0_15px_rgba(239,68,68,0.5)]" />
          <p className="text-5xl font-bold text-white tabular-nums tracking-tight">{data.risk_distribution.find(r => r.name === 'High')?.value || 0}</p>
          <p className="text-xs text-red-400/80 mt-2 uppercase tracking-widest font-semibold">Critical Vulns Detected</p>
        </div>
        <div className="surface-card p-6 flex flex-col items-center justify-center">
          <Target className="w-8 h-8 text-emerald-400 mb-2" />
          <p className="text-5xl font-bold text-white tabular-nums tracking-tight">{data.top_targets.length}</p>
          <p className="text-xs text-slate-400 mt-2 uppercase tracking-widest font-semibold">Unique Targets Surveyed</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="surface-card p-6 h-[400px] flex flex-col">
          <h3 className="text-sm text-slate-300 font-semibold mb-6 flex items-center gap-2 uppercase tracking-wide">
            <Activity className="w-4 h-4 text-indigo-400" /> Scanning Frequency (Timeline)
          </h3>
          <div className="mt-auto flex-1 rounded-2xl border border-white/5 bg-black/20 p-4 flex items-end gap-2">
            {timeline.map((point) => {
              const height = Math.max(8, Math.round((point.scans / maxScans) * 100));
              return (
                <div key={point.date} className="flex-1 flex flex-col items-center justify-end gap-2 min-w-0">
                  <div className="w-full rounded-md bg-indigo-500/70 hover:bg-indigo-400 transition-colors" style={{ height: `${height}%` }} title={`${point.date}: ${point.scans} scans`} />
                  <span className="text-[10px] text-slate-500 truncate w-full text-center">{point.date.slice(5)}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="surface-card p-6 h-[400px] flex flex-col">
          <h3 className="text-sm text-slate-300 font-semibold mb-2 uppercase tracking-wide">Global Risk Distribution</h3>
          <div className="flex-1 flex items-center justify-center gap-8">
            <div className="relative w-52 h-52 shrink-0">
              <div className="absolute inset-0 rounded-full border border-white/10" style={{ background: donutGradient }} />
              <div className="absolute inset-[24%] rounded-full bg-[#0d0d10] border border-white/5 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold text-white">{data.total_scans}</span>
                <span className="text-[10px] text-slate-500 uppercase tracking-widest">Assessments</span>
              </div>
            </div>
            <div className="space-y-2 w-full max-w-[220px]">
              {riskDistribution.map((entry) => (
                <div key={entry.name} className="flex items-center justify-between rounded-xl border border-white/5 bg-black/20 px-3 py-2">
                  <span className="text-xs text-slate-300">{entry.name}</span>
                  <span className="text-xs font-semibold text-white">{entry.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
