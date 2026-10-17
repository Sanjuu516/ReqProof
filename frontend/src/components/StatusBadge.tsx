import React from 'react';
import { VerificationStatus } from '../types';
import { CheckCircle2, AlertTriangle, XCircle, AlertCircle, HelpCircle } from 'lucide-react';

interface Props {
  status: VerificationStatus | string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<Props> = ({ status, size = 'md' }) => {
  const getStyle = () => {
    switch (status) {
      case 'Fully Satisfied':
        return {
          bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          icon: <CheckCircle2 className={size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'} />,
        };
      case 'Partially Satisfied':
        return {
          bg: 'bg-amber-50 text-amber-700 border-amber-200',
          icon: <AlertCircle className={size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'} />,
        };
      case 'Missing':
        return {
          bg: 'bg-rose-50 text-rose-700 border-rose-200',
          icon: <XCircle className={size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'} />,
        };
      case 'Contradictory':
        return {
          bg: 'bg-purple-50 text-purple-700 border-purple-200 font-bold animate-pulse',
          icon: <AlertTriangle className={size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'} />,
        };
      case 'Unverifiable':
      default:
        return {
          bg: 'bg-slate-100 text-slate-600 border-slate-200',
          icon: <HelpCircle className={size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'} />,
        };
    }
  };

  const { bg, icon } = getStyle();
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : size === 'lg' ? 'px-3 py-1.5 text-sm' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${bg} ${sizeClasses}`}>
      {icon}
      <span>{status}</span>
    </span>
  );
};
