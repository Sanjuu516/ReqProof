import React from 'react';
import { ClaimResult, EvidenceRecord } from '../types';
import { StatusBadge } from './StatusBadge';
import { X, FileCode, CheckCircle, XCircle, AlertCircle, Cpu, ExternalLink } from 'lucide-react';

interface Props {
  result: ClaimResult | null;
  onClose: () => void;
}

export const EvidenceModal: React.FC<Props> = ({ result, onClose }) => {
  if (!result) return null;

  const getPolarityBadge = (polarity: string) => {
    switch (polarity) {
      case 'supporting':
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
            <CheckCircle className="w-3 h-3" /> Supporting
          </span>
        );
      case 'contradicting':
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-200">
            <XCircle className="w-3 h-3" /> Contradicting
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
            <AlertCircle className="w-3 h-3" /> Inconclusive
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-5 border-b border-slate-200 flex items-start justify-between bg-slate-50">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
                Claim #{result.claim_id}
              </span>
              <StatusBadge status={result.status} size="sm" />
              <span className="text-xs font-mono text-slate-400">({result.sufficiency_state})</span>
            </div>
            <h2 className="text-base font-semibold text-slate-900 leading-snug">
              {result.claim_text || `Verification Findings for Claim #${result.claim_id}`}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Explanation Box */}
          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5 flex items-center gap-1.5">
              <Cpu className="w-4 h-4 text-sky-600" />
              Deterministic Fusion Rationale
            </h3>
            <p className="text-sm text-slate-700 leading-relaxed font-sans">{result.explanation}</p>
            {result.reason_codes && (
              <div className="mt-2 text-xs font-mono text-slate-500">
                Reason Codes: {result.reason_codes}
              </div>
            )}
          </div>

          {/* Evidence Records */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <FileCode className="w-4 h-4 text-slate-600" />
                Collected Artifact Evidence ({result.evidence_records.length})
              </h3>
            </div>

            {result.evidence_records.length === 0 ? (
              <p className="text-sm text-slate-500 italic p-4 bg-slate-50 rounded-lg border border-slate-100">
                No individual evidence records linked to this claim.
              </p>
            ) : (
              <div className="space-y-3">
                {result.evidence_records.map((ev) => (
                  <div
                    key={ev.evidence_id}
                    className="p-3.5 rounded-lg border border-slate-200 hover:border-slate-300 bg-white transition shadow-xs"
                  >
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold">
                          {ev.evidence_type}
                        </span>
                        {getPolarityBadge(ev.polarity)}
                      </div>
                      <span className="text-[11px] font-mono text-slate-400">
                        {ev.provenance || 'Analyzer'}
                      </span>
                    </div>

                    <p className="text-sm text-slate-800 mb-2 font-medium">{ev.observation}</p>

                    {ev.location_reference && (
                      <div className="flex items-center gap-1 text-xs font-mono text-sky-700 bg-sky-50 px-2.5 py-1 rounded border border-sky-100 w-fit">
                        <ExternalLink className="w-3 h-3" />
                        <span>{ev.location_reference}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-700 hover:text-slate-900 bg-white border border-slate-300 rounded-lg shadow-xs hover:bg-slate-50 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
