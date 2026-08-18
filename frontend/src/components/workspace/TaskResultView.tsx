import React, { useState } from 'react';
import { Button, Badge } from '../ui';
import { AgenticExecutionResult } from '../../api/types';
import {
  CheckCircle2,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  FileText,
  Send,
  Download,
  Share2,
  RotateCcw,
  Sparkles,
  Layers,
  ChevronRight,
  ExternalLink,
  Table,
} from 'lucide-react';

interface TaskResultViewProps {
  result: AgenticExecutionResult;
  onFollowUp: (followUpQuery: string) => void;
  onReset: () => void;
  isLoadingFollowUp?: boolean;
}

export const TaskResultView: React.FC<TaskResultViewProps> = ({
  result,
  onFollowUp,
  onReset,
  isLoadingFollowUp = false,
}) => {
  const [followUpText, setFollowUpText] = useState('');
  const [activeTab, setActiveTab] = useState<'answer' | 'comparisons' | 'evidence' | 'security'>('answer');

  const handleFollowUpSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!followUpText.trim() || isLoadingFollowUp) return;
    onFollowUp(followUpText);
    setFollowUpText('');
  };

  const isBlocked = result.status === 'BLOCKED';
  const hasConflicts = result.conflicts && result.conflicts.length > 0;

  return (
    <div className="w-full space-y-5 animate-fadeIn">
      {/* Result Top Card */}
      <div className="bg-navy-900 border border-navy-700/80 rounded-2xl p-6 shadow-2xl backdrop-blur-md">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-navy-800">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                isBlocked
                  ? 'bg-red-500/10 border border-red-500/30 text-red-400'
                  : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
              }`}
            >
              {isBlocked ? <ShieldAlert className="w-5 h-5" /> : <CheckCircle2 className="w-5 h-5" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-white">
                  {isBlocked ? 'Task Security Action Taken' : 'Task Successfully Executed'}
                </h2>
                <Badge
                  variant={isBlocked ? 'highrisk' : 'safe'}
                  className="text-[11px] font-semibold uppercase tracking-wider"
                >
                  {result.answer_status || result.status}
                </Badge>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Task ID: <code className="text-slate-300 font-mono">{result.task_id}</code> • {result.collected_chunks_count} chunks analyzed across {result.hops_executed} hops
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onReset}
              className="text-xs text-slate-300 hover:text-white flex items-center gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>New Task</span>
            </Button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 pt-4 border-b border-navy-800/80">
          <button
            onClick={() => setActiveTab('answer')}
            className={`text-xs font-medium pb-2.5 px-3 border-b-2 transition-all flex items-center gap-1.5 ${
              activeTab === 'answer'
                ? 'border-blue-500 text-blue-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Summary & Findings</span>
          </button>

          {result.comparisons && result.comparisons.length > 0 && (
            <button
              onClick={() => setActiveTab('comparisons')}
              className={`text-xs font-medium pb-2.5 px-3 border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'comparisons'
                  ? 'border-blue-500 text-blue-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Table className="w-3.5 h-3.5" />
              <span>Dimension Comparisons ({result.comparisons.length})</span>
            </button>
          )}

          {result.citations && result.citations.length > 0 && (
            <button
              onClick={() => setActiveTab('evidence')}
              className={`text-xs font-medium pb-2.5 px-3 border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'evidence'
                  ? 'border-blue-500 text-blue-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Verified Evidence ({result.citations.length})</span>
            </button>
          )}
        </div>

        {/* Tab 1: Executive Summary & Answer */}
        {activeTab === 'answer' && (
          <div className="py-4 space-y-4">
            {/* Executive Summary Box */}
            {result.executive_summary && (
              <div className="bg-navy-950/80 border border-navy-800 rounded-xl p-4">
                <div className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1.5">
                  Executive Summary
                </div>
                <p className="text-sm text-slate-200 leading-relaxed font-medium">
                  {result.executive_summary}
                </p>
              </div>
            )}

            {/* Detailed Answer */}
            {result.detailed_answer && (
              <div className="bg-navy-950/40 rounded-xl p-4 border border-navy-800/60">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Detailed Findings & Provenance
                </div>
                <div className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
                  {result.detailed_answer}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {result.recommendations && result.recommendations.length > 0 && (
              <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4">
                <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Actionable Recommendations</span>
                </div>
                <ul className="space-y-1.5">
                  {result.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-xs text-slate-200 flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Conflicts / Discrepancies if any */}
            {hasConflicts && (
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
                <div className="text-xs font-semibold text-amber-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Source Discrepancies Preserved</span>
                </div>
                <div className="space-y-1 text-xs text-slate-300">
                  {result.conflicts.map((conf, idx) => (
                    <div key={idx} className="p-2 rounded bg-navy-950/60 border border-amber-500/20">
                      {typeof conf === 'string' ? conf : JSON.stringify(conf)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Dimension Comparisons */}
        {activeTab === 'comparisons' && result.comparisons && (
          <div className="py-4">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-navy-800 bg-navy-950/60 text-[11px] text-slate-400 uppercase tracking-wider">
                    <th className="p-3">Dimension</th>
                    <th className="p-3">Candidate / Option A</th>
                    <th className="p-3">Candidate / Option B</th>
                    <th className="p-3">Comparative Verdict</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-navy-800/60 text-xs">
                  {result.comparisons.map((comp, idx) => (
                    <tr key={idx} className="hover:bg-navy-950/40 transition-colors">
                      <td className="p-3 font-medium text-slate-200">{comp.dimension}</td>
                      <td className="p-3 text-slate-300">{comp.entity_a_value}</td>
                      <td className="p-3 text-slate-300">{comp.entity_b_value}</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 font-medium">
                          {comp.comparison_verdict}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Verified Evidence Citations */}
        {activeTab === 'evidence' && result.citations && (
          <div className="py-4 space-y-3">
            {result.citations.map((cit, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-navy-950/80 border border-navy-800 text-xs space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="neutral" className="text-[10px] font-mono">
                      {cit.citation_id || `[CIT-${idx + 1}]`}
                    </Badge>
                    <span className="font-semibold text-slate-200">{cit.document_id}</span>
                  </div>
                  <span className="text-[11px] text-slate-500 font-mono">{cit.source}</span>
                </div>
                <p className="text-slate-300 bg-navy-900/60 p-2 rounded border border-navy-850 font-mono text-[11px]">
                  "{cit.snippet}"
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Natural-Language Follow-up Bar */}
      <div className="bg-navy-900 border border-navy-700/80 rounded-2xl p-4 shadow-xl">
        <div className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          <span>Ask a natural-language follow-up on this result</span>
        </div>

        <form onSubmit={handleFollowUpSubmit} className="flex items-center gap-2">
          <input
            type="text"
            value={followUpText}
            onChange={(e) => setFollowUpText(e.target.value)}
            disabled={isLoadingFollowUp}
            placeholder="e.g. Now show me only candidates with CISSP, or Why is Sarah above David?"
            className="flex-1 bg-navy-950/80 border border-navy-700 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
          />
          <Button
            type="submit"
            disabled={!followUpText.trim() || isLoadingFollowUp}
            isLoading={isLoadingFollowUp}
            variant="primary"
            className="px-4 py-2.5 rounded-xl text-xs font-medium flex items-center gap-1.5"
          >
            <span>Ask Follow-up</span>
            <Send className="w-3.5 h-3.5" />
          </Button>
        </form>
      </div>
    </div>
  );
};
