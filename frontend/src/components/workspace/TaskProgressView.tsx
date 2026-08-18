import React, { useState } from 'react';
import { Card, Badge } from '../ui';
import {
  CheckCircle2,
  Loader2,
  Clock,
  ShieldCheck,
  Search,
  CheckCheck,
  FileCheck,
  ChevronDown,
  ChevronUp,
  Cpu,
} from 'lucide-react';

export type TaskExecutionPhase =
  | 'UNDERSTANDING'
  | 'SECURITY_SCAN'
  | 'FILTERING'
  | 'RETRIEVAL'
  | 'VERIFICATION'
  | 'SYNTHESIS'
  | 'COMPLETE';

interface TaskProgressViewProps {
  currentPhase: TaskExecutionPhase;
  taskTitle: string;
  stats?: {
    scannedCount?: number;
    safeCount?: number;
    highRiskCount?: number;
    hopsExecuted?: number;
  };
}

export const TaskProgressView: React.FC<TaskProgressViewProps> = ({
  currentPhase,
  taskTitle,
  stats,
}) => {
  const [showHowItWorks, setShowHowItWorks] = useState(false);

  const phases = [
    { id: 'UNDERSTANDING', label: 'Understanding Task & Formulating Plan', icon: Clock },
    { id: 'SECURITY_SCAN', label: 'Scanning Documents for Security Threats', icon: ShieldCheck },
    { id: 'FILTERING', label: 'Quarantining Unsafe & Uninspectable Files', icon: ShieldCheck },
    { id: 'RETRIEVAL', label: 'Adaptive Multi-Hop Retrieval & Evidence Fusion', icon: Search },
    { id: 'VERIFICATION', label: 'Groundedness & Atomic Claim Verification', icon: CheckCheck },
    { id: 'SYNTHESIS', label: 'Research Synthesis & Reasoning Finalization', icon: FileCheck },
  ];

  const getPhaseStatus = (phaseId: string) => {
    const phaseOrder = [
      'UNDERSTANDING',
      'SECURITY_SCAN',
      'FILTERING',
      'RETRIEVAL',
      'VERIFICATION',
      'SYNTHESIS',
      'COMPLETE',
    ];
    const currentIndex = phaseOrder.indexOf(currentPhase);
    const targetIndex = phaseOrder.indexOf(phaseId);

    if (currentPhase === 'COMPLETE' || currentIndex > targetIndex) return 'COMPLETED';
    if (currentIndex === targetIndex) return 'ACTIVE';
    return 'PENDING';
  };

  return (
    <div className="w-full bg-navy-900 border border-navy-700/80 rounded-2xl p-6 shadow-2xl my-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-navy-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Loader2 className="w-4 h-4 animate-spin" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              Executing Task: <span className="text-slate-300 font-normal">{taskTitle}</span>
            </h3>
            <p className="text-xs text-slate-400">
              Autonomous execution across security, multi-hop retrieval, and evidence verification.
            </p>
          </div>
        </div>

        <Badge variant="info" className="flex items-center gap-1.5 py-1 px-3">
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
          <span className="text-xs font-medium text-blue-300">In Progress</span>
        </Badge>
      </div>

      {/* Real Execution Steps List */}
      <div className="space-y-3 my-4">
        {phases.map((phase) => {
          const status = getPhaseStatus(phase.id);
          const Icon = phase.icon;
          return (
            <div
              key={phase.id}
              className={`flex items-center justify-between p-3 rounded-xl border transition-all ${
                status === 'ACTIVE'
                  ? 'bg-blue-500/10 border-blue-500/30 text-blue-300 shadow-sm'
                  : status === 'COMPLETED'
                  ? 'bg-navy-950/60 border-navy-800 text-slate-200'
                  : 'bg-navy-950/30 border-navy-900 text-slate-500'
              }`}
            >
              <div className="flex items-center gap-3">
                {status === 'COMPLETED' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : status === 'ACTIVE' ? (
                  <Loader2 className="w-4 h-4 text-blue-400 animate-spin shrink-0" />
                ) : (
                  <div className="w-4 h-4 rounded-full border border-slate-600 shrink-0" />
                )}
                <span className="text-xs font-medium">{phase.label}</span>
              </div>

              <div className="text-[11px] uppercase tracking-wider font-semibold">
                {status === 'COMPLETED' && <span className="text-emerald-400">Done</span>}
                {status === 'ACTIVE' && <span className="text-blue-400 animate-pulse">Running</span>}
                {status === 'PENDING' && <span className="text-slate-600">Pending</span>}
              </div>
            </div>
          );
        })}
      </div>

      {/* Authoritative Live Counters */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pt-2 border-t border-navy-800/80">
          <div className="bg-navy-950/80 p-2.5 rounded-lg text-center">
            <div className="text-[10px] text-slate-400 font-medium">Scanned Items</div>
            <div className="text-sm font-bold text-slate-200">{stats.scannedCount || 0}</div>
          </div>
          <div className="bg-navy-950/80 p-2.5 rounded-lg text-center">
            <div className="text-[10px] text-slate-400 font-medium">Safe Items</div>
            <div className="text-sm font-bold text-emerald-400">{stats.safeCount || 0}</div>
          </div>
          <div className="bg-navy-950/80 p-2.5 rounded-lg text-center">
            <div className="text-[10px] text-slate-400 font-medium">High Risk (Quarantined)</div>
            <div className="text-sm font-bold text-red-400">{stats.highRiskCount || 0}</div>
          </div>
          <div className="bg-navy-950/80 p-2.5 rounded-lg text-center">
            <div className="text-[10px] text-slate-400 font-medium">Retrieval Hops</div>
            <div className="text-sm font-bold text-blue-400">{stats.hopsExecuted || 1}</div>
          </div>
        </div>
      )}

      {/* Optional "How SECUROXI is Working" Dropdown */}
      <div className="mt-4 pt-3 border-t border-navy-800/60">
        <button
          onClick={() => setShowHowItWorks(!showHowItWorks)}
          className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition-colors"
        >
          <Cpu className="w-3.5 h-3.5 text-blue-400" />
          <span>How SECUROXI is working under the hood</span>
          {showHowItWorks ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {showHowItWorks && (
          <div className="mt-2.5 p-3 rounded-lg bg-navy-950/90 border border-navy-800 text-xs text-slate-300 space-y-1.5 animate-fadeIn">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span><strong>Security Analysis</strong>: Deterministic threat detection & OCR visual scan.</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              <span><strong>Adaptive Retrieval</strong>: Iterative multi-hop strategy addressing evidence gaps.</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
              <span><strong>Evidence Fusion</strong>: Source authority calibration & contradiction resolution.</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              <span><strong>Grounded Verification</strong>: Atomic claim validation ensuring 0% hallucination.</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
