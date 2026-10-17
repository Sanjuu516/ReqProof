import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { ShieldCheck, LogOut, FolderKanban, Database, KeyRound, X, Check, Server, Users } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [showDbModal, setShowDbModal] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [dbData, setDbData] = useState<any>(null);
  const [geminiStatus, setGeminiStatus] = useState<any>(null);
  const [newKey, setNewKey] = useState('');
  const [keySaved, setKeySaved] = useState(false);

  useEffect(() => {
    if (user) {
      api.getGeminiStatus().then(setGeminiStatus).catch(() => {});
    }
  }, [user]);

  const openDbModal = async () => {
    try {
      const data = await api.getDatabaseOverview();
      setDbData(data);
      setShowDbModal(true);
    } catch (e: any) {
      alert('Failed to load database overview: ' + e.message);
    }
  };

  const handleSaveKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim()) return;
    try {
      await api.updateGeminiKey(newKey.trim());
      const updated = await api.getGeminiStatus();
      setGeminiStatus(updated);
      setKeySaved(true);
      setTimeout(() => {
        setKeySaved(false);
        setShowKeyModal(false);
      }, 1500);
    } catch (e: any) {
      alert('Failed to save key: ' + e.message);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <>
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-lg bg-sky-600 flex items-center justify-center text-white shadow-sm group-hover:bg-sky-700 transition">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-lg text-slate-900 tracking-tight flex items-center gap-1.5">
                ReqProof
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-sky-100 text-sky-700 font-semibold">MVP</span>
              </span>
              <p className="text-xs text-slate-500 leading-none">Multi-Artifact Verification</p>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            {/* Database Inspector Button - Always Visible */}
            <button
              onClick={openDbModal}
              className="text-xs font-semibold text-slate-700 hover:text-slate-900 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-800 flex items-center gap-1.5 py-1.5 px-3 rounded-lg shadow-2xs transition"
              title="Inspect SQLite Database, Tables & User Accounts"
            >
              <Database className="w-3.5 h-3.5 text-emerald-600" />
              <span>Database Details</span>
            </button>

            {/* Gemini Key Button - Always Visible */}
            <button
              onClick={() => setShowKeyModal(true)}
              className={`text-xs font-semibold flex items-center gap-1.5 py-1.5 px-3 rounded-lg border transition shadow-2xs ${
                geminiStatus?.configured
                  ? 'bg-sky-50 text-sky-700 border-sky-200 hover:bg-sky-100'
                  : 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100'
              }`}
              title="Configure Google Gemini API Key"
            >
              <KeyRound className="w-3.5 h-3.5" />
              <span>{geminiStatus?.configured ? 'Gemini: Active' : 'Gemini: Heuristic'}</span>
            </button>

            {user ? (
              <>
                <Link
                  to="/projects"
                  className="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1.5 py-1.5 px-3 rounded-md hover:bg-slate-100 transition"
                >
                  <FolderKanban className="w-4 h-4" />
                  Projects
                </Link>

                <div className="h-4 w-px bg-slate-200"></div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-xs font-semibold text-slate-800 leading-none">{user.name}</p>
                    <p className="text-[11px] text-slate-400 font-mono mt-0.5">{user.email}</p>
                  </div>
                  <button
                    onClick={handleLogout}
                    title="Logout"
                    className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="text-xs font-semibold text-slate-600 hover:text-slate-900 px-3 py-1.5 rounded-md hover:bg-slate-100 transition"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="text-xs font-semibold text-white bg-sky-600 hover:bg-sky-700 px-3 py-1.5 rounded-lg shadow-xs transition"
                >
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Database Inspector Modal */}
      {showDbModal && dbData && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-emerald-600" />
                <h2 className="text-base font-bold text-slate-900">Database & Authentication Inspector</h2>
              </div>
              <button onClick={() => setShowDbModal(false)} className="p-1 text-slate-400 hover:text-slate-600 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-6">
              {/* Storage Info */}
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 text-xs font-mono space-y-1.5">
                <div className="flex items-center gap-2 text-slate-700">
                  <Server className="w-4 h-4 text-emerald-600" />
                  <span className="font-bold">Database Type:</span> {dbData.database_type}
                </div>
                <div className="text-slate-600 break-all">
                  <span className="font-bold">File Location:</span> {dbData.database_storage_location}
                </div>
              </div>

              {/* Table Record Counts */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Table Records</h3>
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  {Object.entries(dbData.tables).map(([tbl, count]: any) => (
                    <div key={tbl} className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                      <p className="font-bold text-slate-900 text-sm">{count}</p>
                      <p className="text-[11px] font-mono text-slate-500 capitalize">{tbl.replace('_', ' ')}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Registered Users */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
                  <Users className="w-3.5 h-3.5 text-slate-500" /> Registered Users & Auth Hashes
                </h3>
                <div className="border border-slate-200 rounded-lg overflow-hidden text-xs">
                  <table className="w-full text-left">
                    <thead className="bg-slate-50 font-mono text-slate-500 uppercase text-[10px] border-b border-slate-200">
                      <tr>
                        <th className="p-2.5">User ID</th>
                        <th className="p-2.5">Name</th>
                        <th className="p-2.5">Email</th>
                        <th className="p-2.5">Password Hash (PBKDF2)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {dbData.registered_users.map((u: any) => (
                        <tr key={u.user_id}>
                          <td className="p-2.5 font-mono text-slate-400">#{u.user_id}</td>
                          <td className="p-2.5 font-medium text-slate-800">{u.name}</td>
                          <td className="p-2.5 text-slate-600">{u.email}</td>
                          <td className="p-2.5 font-mono text-slate-400 text-[10px]">{u.password_hash_preview}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end">
              <button
                onClick={() => setShowDbModal(false)}
                className="px-4 py-2 text-xs font-semibold bg-white border border-slate-300 text-slate-700 rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Gemini Key Modal */}
      {showKeyModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <KeyRound className="w-4 h-4 text-sky-600" /> Google Gemini API Settings
              </h2>
              <button onClick={() => setShowKeyModal(false)} className="p-1 text-slate-400 hover:text-slate-600 rounded">
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-slate-500 mb-4 leading-relaxed">
              Gemini decomposes natural-language requirements into atomic claims. If not provided, ReqProof automatically uses its built-in offline heuristic parser so the system never fails!
            </p>

            <form onSubmit={handleSaveKey} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  API Key
                </label>
                <input
                  type="password"
                  placeholder="Paste your AIzaSy... key here"
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  className="mt-1.5 block w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 text-xs font-mono focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <div className="p-3 bg-sky-50 rounded-lg border border-sky-200 text-[11px] text-sky-800">
                <p className="font-semibold mb-0.5">Where to get a key?</p>
                Get a free key from <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" className="underline font-bold">Google AI Studio</a>. Free keys do not expire unless revoked.
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowKeyModal(false)}
                  className="px-3.5 py-2 text-xs font-medium text-slate-600 bg-white border border-slate-300 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold text-white bg-sky-600 hover:bg-sky-700 rounded-lg flex items-center gap-1.5"
                >
                  {keySaved ? <><Check className="w-3.5 h-3.5" /> Saved!</> : 'Save Key'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
