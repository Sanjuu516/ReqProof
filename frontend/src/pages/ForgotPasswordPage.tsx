import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { ShieldCheck, Mail, ArrowLeft, CheckCircle, AlertCircle, ExternalLink } from 'lucide-react';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setError('');
    setLoading(true);

    try {
      const res = await api.forgotPassword(email.trim());
      setResponse(res);
    } catch (err: any) {
      setError(err.message || 'Failed to request password reset');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="w-12 h-12 rounded-xl bg-sky-600 flex items-center justify-center text-white mx-auto shadow-md">
          <ShieldCheck className="w-7 h-7" />
        </div>
        <h2 className="mt-4 text-2xl font-bold tracking-tight text-slate-900">Forgot Your Password?</h2>
        <p className="mt-1 text-sm text-slate-500">
          Enter your registered Gmail or email address to receive a secure reset link
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-slate-200 rounded-xl sm:px-10">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 flex items-center gap-2 text-rose-700 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {response ? (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-bold text-emerald-900">Reset Request Dispatched!</h4>
                  <p className="text-xs text-emerald-700 mt-0.5">
                    {response.message}
                  </p>
                </div>
              </div>

              {response.delivery?.reset_url && (
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <span className="text-[11px] font-mono font-bold uppercase text-slate-500 block">
                    Local Test Preview
                  </span>
                  <p className="text-xs text-slate-600">
                    You can click the link below to immediately test the reset flow:
                  </p>
                  <a
                    href={response.delivery.reset_url}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-sky-600 hover:text-sky-700 hover:underline break-all"
                  >
                    <span>{response.delivery.reset_url}</span>
                    <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                  </a>
                </div>
              )}

              <div className="pt-2 text-center">
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-sky-600 hover:text-sky-700"
                >
                  <ArrowLeft className="w-3.5 h-3.5" /> Back to Sign In
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  placeholder="e.g. yourname@gmail.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-1.5 block w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500 transition"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center items-center gap-2 py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-sky-600 hover:bg-sky-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 disabled:opacity-50 transition"
              >
                <Mail className="w-4 h-4" />
                {loading ? 'Sending Reset Instructions...' : 'Send Reset Link'}
              </button>

              <div className="pt-2 text-center">
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800"
                >
                  <ArrowLeft className="w-3.5 h-3.5" /> Back to Sign In
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
