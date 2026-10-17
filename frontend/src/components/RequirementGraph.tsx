import React from 'react';
import { RequirementGraph as GraphData } from '../types';
import { StatusBadge } from './StatusBadge';
import { Layers, ArrowRight } from 'lucide-react';

interface Props {
  graph: GraphData;
}

export const RequirementGraphView: React.FC<Props> = ({ graph }) => {
  const reqNodes = graph.nodes.filter((n) => n.type === 'requirement');
  const claimNodes = graph.nodes.filter((n) => n.type === 'claim');

  if (graph.nodes.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500 bg-white rounded-xl border border-dashed border-slate-300">
        <Layers className="w-8 h-8 mx-auto mb-2 text-slate-400" />
        <p className="font-medium">No requirement nodes found in graph.</p>
        <p className="text-xs text-slate-400 mt-1">Add a requirement to see its decomposition hierarchy.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-100">
        <div>
          <h3 className="text-base font-bold text-slate-900">Requirement Dependency & Decomposition Graph</h3>
          <p className="text-xs text-slate-500">Visual mapping between high-level requirements and atomic verifiable claims</p>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-sky-500 inline-block"></span> Requirement</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-indigo-500 inline-block"></span> Atomic Claim</span>
        </div>
      </div>

      <div className="space-y-6">
        {reqNodes.map((reqNode) => {
          // Find claims linked to this requirement
          const linkedClaimIds = graph.edges
            .filter((e) => e.source === reqNode.id)
            .map((e) => e.target);
          const childClaims = claimNodes.filter((c) => linkedClaimIds.includes(c.id));

          return (
            <div key={reqNode.id} className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
              {/* Parent Node */}
              <div className="p-4 bg-white rounded-lg border-2 border-sky-400 shadow-xs mb-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-mono font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded">
                    REQUIREMENT #{reqNode.data?.id}
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono">{reqNode.data?.created_at?.slice(0, 10)}</span>
                </div>
                <p className="text-sm font-semibold text-slate-900 mt-1">{reqNode.data?.text}</p>
              </div>

              {/* Children Claims */}
              <div className="pl-6 border-l-2 border-dashed border-sky-300 ml-4 space-y-3">
                <div className="text-[11px] font-mono font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                  <ArrowRight className="w-3 h-3 text-sky-500" /> Decomposed Atomic Claims ({childClaims.length})
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {childClaims.map((claim) => (
                    <div
                      key={claim.id}
                      className="p-3 bg-white rounded-lg border border-slate-200 hover:border-indigo-300 shadow-2xs transition"
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[11px] font-mono font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded">
                          CLAIM #{claim.data?.id}
                        </span>
                        {claim.data?.status && claim.data.status !== 'unverified' ? (
                          <StatusBadge status={claim.data.status} size="sm" />
                        ) : (
                          <span className="text-[10px] font-mono text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                            Pending Run
                          </span>
                        )}
                      </div>
                      <p className="text-xs font-medium text-slate-800 line-clamp-2">{claim.data?.text}</p>
                      {claim.data?.expected_behavior && (
                        <p className="text-[11px] text-slate-500 mt-1 line-clamp-1 italic">
                          Expected: {claim.data.expected_behavior}
                        </p>
                      )}
                      <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] font-mono text-slate-400">
                        <span>Artifacts: {claim.data?.artifact_types || 'all'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
