import React, { useState, useEffect } from 'react';
import { Shield, Trash2, ArrowUpCircle } from 'lucide-react';

export default function AdminPanel({ authData }) {
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/users`, {
        headers: { 'Authorization': `Bearer ${authData.token}` }
      });
      const data = await res.json();
      if (data.ok) setUsers(data.users);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleDelete = async (id) => {
    await fetch(`${API_BASE_URL}/api/admin/users/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${authData.token}` }
    });
    fetchUsers();
  };

  const handlePromote = async (id) => {
    await fetch(`${API_BASE_URL}/api/admin/users/${id}/promote`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${authData.token}` }
    });
    fetchUsers();
  };

  if (authData.role !== 'admin') {
    return <div className="text-center py-20 text-red-400">UNAUTHORIZED ACCESS ATTEMPT DETECTED. EXCEEDING CLEARANCE.</div>;
  }

  return (
    <div className="max-w-5xl mx-auto pb-12 w-full">
      <div className="glass-panel p-8">
         <h2 className="text-xl font-bold text-white flex items-center gap-3 mb-6">
          <Shield className="w-6 h-6 text-indigo-400" />
          Access Control Matrix
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-white/5 text-slate-400">
              <tr>
                <th className="p-4 rounded-tl-xl font-medium tracking-wide">Username</th>
                <th className="p-4 font-medium tracking-wide">Clearance Level</th>
                <th className="p-4 rounded-tr-xl font-medium text-right tracking-wide">Administrative Override</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-slate-300">
              {users.map(u => (
                <tr key={u.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="p-4 font-medium">{u.username}</td>
                  <td className="p-4">
                     <span className={`px-2.5 py-1 rounded-lg text-xs font-bold tracking-wider ${u.role === 'admin' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'bg-slate-500/10 text-slate-400 border border-slate-500/20'}`}>
                       {u.role.toUpperCase()}
                     </span>
                  </td>
                  <td className="p-4 flex gap-2 justify-end">
                    {u.role !== 'admin' && (
                      <button onClick={() => handlePromote(u.id)} className="p-2 bg-indigo-500/10 hover:bg-indigo-500 text-indigo-400 hover:text-white rounded-lg transition-colors border border-indigo-500/20" title="Promote to Admin">
                        <ArrowUpCircle className="w-4 h-4" />
                      </button>
                    )}
                    <button onClick={() => handleDelete(u.id)} className="p-2 bg-red-500/10 hover:bg-red-500 text-red-400 hover:text-white rounded-lg transition-colors border border-red-500/20" title="Revoke Clearance">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {loading && <div className="w-full text-center py-10 text-slate-500">Querying identity provider...</div>}
        </div>
      </div>
    </div>
  );
}
