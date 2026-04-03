import React, { useCallback, useEffect, useState } from 'react';
import { Clock, Plus, Trash2, Globe, ShieldCheck } from 'lucide-react';

export default function Autopilot({ authData }) {
  const [scans, setScans] = useState([]);
  const [target, setTarget] = useState('');
  const [intervalOption, setIntervalOption] = useState(24);
  const [loading, setLoading] = useState(true);

  const fetchScans = useCallback(async () => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/schedule`, {
        headers: { 'Authorization': `Bearer ${authData.token}` }
      });
      const data = await res.json();
      if (data.ok) setScans(data.scans || []);
    } finally {
      setLoading(false);
    }
  }, [authData.token]);

  useEffect(() => {
    fetchScans();
  }, [fetchScans]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!target) return;
    await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/schedule`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authData.token}`
      },
      body: JSON.stringify({ target, interval: parseInt(intervalOption) })
    });
    setTarget('');
    fetchScans();
  };

  const handleDelete = async (id) => {
    await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/schedule/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${authData.token}` }
    });
    fetchScans();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12 w-full">
      <div className="surface-card p-8">
        <h2 className="text-xl font-bold text-white flex items-center gap-3 mb-6">
          <Clock className="w-6 h-6 text-indigo-400" />
          Autopilot Engine
        </h2>
        <p className="subtle-text mb-8">
          Configure continuous, headless vulnerability assessments. The Python backend scheduler will autonomously port-scan and fingerprint targets on your defined interval, routing the output silently into the encrypted `SQLite` datastore.
        </p>

        <form onSubmit={handleAdd} className="flex flex-col md:flex-row gap-4 mb-2">
          <div className="flex-1">
            <input
              type="text"
              className="input-field w-full"
              placeholder="Target hostname (e.g. scanme.nmap.org)"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              required
            />
          </div>
          <div className="w-full md:w-48">
            <select
              className="input-field w-full appearance-none bg-[#1A1A1D]"
              value={intervalOption}
              onChange={(e) => setIntervalOption(e.target.value)}
            >
              <option value="6">Every 6 Hours</option>
              <option value="12">Every 12 Hours</option>
              <option value="24">Every 24 Hours</option>
              <option value="168">Weekly (168 Hrs)</option>
            </select>
          </div>
          <button type="submit" className="btn-primary flex items-center justify-center gap-2 md:w-32">
            <Plus className="w-5 h-5" /> Queue
          </button>
        </form>
      </div>

      <div className="surface-card p-8 min-h-[300px]">
        <h3 className="section-title mb-6">Active Autonomous Directives</h3>
        
        {loading ? (
          <div className="text-center py-10 text-slate-500 animate-pulse">Syncing chronological schedules...</div>
        ) : scans.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-white/5 rounded-2xl bg-white/[0.01]">
            <ShieldCheck className="w-8 h-8 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">No scheduled scans are currently queued in the autonomous engine.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {scans.map((scan) => (
              <div key={scan.id} className="flex items-center justify-between bg-[#151518]/90 border border-white/5 p-4 rounded-xl hover:border-indigo-500/20 transition-all">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                    <Globe className="w-4 h-4 text-indigo-400" />
                  </div>
                  <div>
                    <h4 className="text-slate-200 font-medium">{scan.target}</h4>
                    <p className="text-xs text-indigo-400 mt-0.5 tracking-wide">Runs every {scan.interval} hours (Owner: {scan.operator})</p>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(scan.id)}
                  className="p-2.5 bg-red-500/10 hover:bg-red-500 hover:text-white text-red-400 rounded-lg transition-colors border border-red-500/20"
                  title="Purge Task"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
