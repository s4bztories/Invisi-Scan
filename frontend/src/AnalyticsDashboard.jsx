import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Activity, ShieldAlert, Target, Database } from 'lucide-react';

const COLORS = ['#ef4444', '#f59e0b', '#10b981']; // High, Medium, Low

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

  if (loading) return <div className="text-white text-center py-20 animate-pulse">Initializing Global Uplink...</div>;
  if (!data) return <div className="text-red-400 text-center py-20">Failed to establish connection to Command Center.</div>;

  return (
    <div className="space-y-6 pb-12 w-full">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel p-6 flex flex-col items-center justify-center">
          <Database className="w-8 h-8 text-indigo-400 mb-2" />
          <p className="text-5xl font-bold text-white tabular-nums tracking-tight">{data.total_scans}</p>
          <p className="text-xs text-slate-400 mt-2 uppercase tracking-widest font-semibold">Total Scans Performed</p>
        </div>
        <div className="glass-panel p-6 flex flex-col items-center justify-center">
          <ShieldAlert className="w-8 h-8 text-red-500 mb-2 drop-shadow-[0_0_15px_rgba(239,68,68,0.5)]" />
          <p className="text-5xl font-bold text-white tabular-nums tracking-tight">{data.risk_distribution.find(r => r.name === 'High')?.value || 0}</p>
          <p className="text-xs text-red-400/80 mt-2 uppercase tracking-widest font-semibold">Critical Vulns Detected</p>
        </div>
        <div className="glass-panel p-6 flex flex-col items-center justify-center">
          <Target className="w-8 h-8 text-emerald-400 mb-2" />
          <p className="text-5xl font-bold text-white tabular-nums tracking-tight">{data.top_targets.length}</p>
          <p className="text-xs text-slate-400 mt-2 uppercase tracking-widest font-semibold">Unique Targets Surveyed</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-panel p-6 h-[400px]">
          <h3 className="text-sm text-slate-300 font-semibold mb-6 flex items-center gap-2 uppercase tracking-wide">
            <Activity className="w-4 h-4 text-indigo-400" /> Scanning Frequency (Timeline)
          </h3>
          <ResponsiveContainer width="100%" height="85%">
            <AreaChart data={data.timeline} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorScans" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#818cf8" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#818cf8" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="date" stroke="#475569" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#475569" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1A1A1D', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)' }} 
                itemStyle={{ color: '#fff' }}
              />
              <Area type="monotone" dataKey="scans" stroke="#818cf8" strokeWidth={3} fillOpacity={1} fill="url(#colorScans)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-panel p-6 h-[400px] flex flex-col">
          <h3 className="text-sm text-slate-300 font-semibold mb-2 uppercase tracking-wide">Global Risk Distribution</h3>
          <div className="flex-1 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie 
                  data={data.risk_distribution.filter(d => d.value > 0)} 
                  innerRadius={100} 
                  outerRadius={130} 
                  paddingAngle={8} 
                  dataKey="value" 
                  stroke="none"
                  cornerRadius={6}
                >
                  {data.risk_distribution.filter(d => d.value > 0).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[data.risk_distribution.findIndex(r => r.name === entry.name)]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1A1A1D', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px' }} 
                  itemStyle={{ color: '#fff', fontWeight: 'bold' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-4xl font-bold text-white drop-shadow-md">{data.total_scans}</span>
              <span className="text-xs text-slate-500 uppercase tracking-widest mt-1 font-semibold">Assessments</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
