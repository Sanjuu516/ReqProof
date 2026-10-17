import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, LogOut, FolderKanban, PlusCircle } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
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

        {user && (
          <div className="flex items-center gap-4">
            <Link
              to="/projects"
              className="text-sm font-medium text-slate-600 hover:text-slate-900 flex items-center gap-1.5 py-1.5 px-3 rounded-md hover:bg-slate-100 transition"
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
          </div>
        )}
      </div>
    </header>
  );
};
