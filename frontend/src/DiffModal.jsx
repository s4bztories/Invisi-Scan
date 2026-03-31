import React from 'react';
import { Shield, ChevronRight, AlertTriangle, X, CheckCircle } from 'lucide-react';

export default function DiffModal({ data, onClose }) {
  if (!data) return null;
  const { older, newer } = data;

  const oldPorts = older.report_json.open_ports || [];
  const newPorts = newer.report_json.open_ports || [];

  const addedPorts = newPorts.filter(p => !oldPorts.includes(p));
  const removedPorts = oldPorts.filter(p => !newPorts.includes(p));
  const commonPorts = oldPorts.filter(p => newPorts.includes(p));

  const countCVEs = (report, port) => {
    if (!report.report_json.cves || !report.report_json.cves[port]) return 0;
    return report.report_json.cves[port].length;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-[#0f0f13] border border-white/10 rounded-2xl w-full max-w-4xl max-h-[85vh] overflow-hidden flex flex-col shadow-2xl">
        
        <div className="p-6 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Shield className="w-5 h-5 text-indigo-400" /> Historical Delta Analysis
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              Comparing <strong>{older.target}</strong>
            </p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-xl transition-all">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          
          <div className="flex items-center justify-between bg-white/[0.02] p-4 rounded-xl border border-white/5">
            <div className="text-center flex-1">
              <span className="block text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1">Baseline</span>
              <span className="text-sm text-slate-300">{new Date(older.timestamp).toLocaleString()}</span>
            </div>
            <div className="px-4 text-slate-600">
               <ChevronRight className="w-6 h-6" />
            </div>
            <div className="text-center flex-1">
              <span className="block text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1">Current</span>
              <span className="text-sm text-indigo-300 font-medium">{new Date(newer.timestamp).toLocaleString()}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
             <div className="space-y-4">
               <h3 className="text-sm font-semibold text-red-400 flex items-center gap-2 border-b border-red-500/10 pb-2">
                 Issues Added / Regressions
               </h3>
               {addedPorts.length === 0 && <p className="text-xs text-slate-500">No new ports opened.</p>}
               {addedPorts.map(p => (
                 <div key={`add-port-${p}`} className="bg-red-500/10 border border-red-500/20 p-3 rounded-xl flex justify-between">
                   <span className="text-red-300 font-mono text-sm">+ Port {p} Opened</span>
                   <span className="text-xs text-red-400 font-bold">{countCVEs(newer, p)} CVEs</span>
                 </div>
               ))}
               {commonPorts.map(p => {
                 const diff = countCVEs(newer, p) - countCVEs(older, p);
                 if (diff > 0) {
                   return (
                     <div key={`cve-up-${p}`} className="bg-orange-500/10 border border-orange-500/20 p-3 rounded-xl flex justify-between">
                       <span className="text-orange-300 text-sm">Port {p} Vulnerabilities</span>
                       <span className="text-xs text-orange-400 font-bold">+{diff} CVEs</span>
                     </div>
                   );
                 }
                 return null;
               })}
             </div>

             <div className="space-y-4">
               <h3 className="text-sm font-semibold text-emerald-400 flex items-center gap-2 border-b border-emerald-500/10 pb-2">
                 Issues Resolved
               </h3>
               {removedPorts.length === 0 && <p className="text-xs text-slate-500">No ports closed.</p>}
               {removedPorts.map(p => (
                 <div key={`rem-port-${p}`} className="bg-emerald-500/10 border border-emerald-500/20 p-3 rounded-xl flex justify-between">
                   <span className="text-emerald-300 font-mono text-sm">- Port {p} Closed</span>
                   <CheckCircle className="w-4 h-4 text-emerald-400" />
                 </div>
               ))}
               {commonPorts.map(p => {
                 const diff = countCVEs(older, p) - countCVEs(newer, p);
                 if (diff > 0) {
                   return (
                     <div key={`cve-down-${p}`} className="bg-emerald-500/10 border border-emerald-500/20 p-3 rounded-xl flex justify-between">
                       <span className="text-emerald-300 text-sm">Port {p} Vulnerabilities</span>
                       <span className="text-xs text-emerald-400 font-bold">-{diff} CVEs</span>
                     </div>
                   );
                 }
                 return null;
               })}
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
