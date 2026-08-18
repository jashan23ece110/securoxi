import React from 'react';
import { Button, Badge } from '../ui';
import { TaskUnderstandingPreview } from '../../api/types';
import {
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Play,
  Edit3,
  ShieldAlert,
  Sliders,
  Check,
} from 'lucide-react';

interface TaskUnderstandingViewProps {
  understanding: TaskUnderstandingPreview;
  onConfirm: () => void;
  onEdit: () => void;
  onSelectClarification?: (question: string, answer: string) => void;
  isExecuting?: boolean;
}

export const TaskUnderstandingView: React.FC<TaskUnderstandingViewProps> = ({
  understanding,
  onConfirm,
  onEdit,
  onSelectClarification,
  isExecuting = false,
}) => {
  return (
    <div className="w-full bg-navy-900 border border-navy-700 rounded-2xl p-6 shadow-xl my-4 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-navy-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              Task Interpretation Preview
            </h3>
            <p className="text-xs text-slate-400">
              SECUROXI formulated the following structured execution plan:
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onEdit}
            disabled={isExecuting}
            className="text-xs text-slate-300 hover:text-white flex items-center gap-1.5"
          >
            <Edit3 className="w-3.5 h-3.5" />
            <span>Edit</span>
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={onConfirm}
            isLoading={isExecuting}
            className="text-xs font-medium flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Confirm & Execute</span>
          </Button>
        </div>
      </div>

      {/* Grid of Understood Dimensions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-5">
        {/* Intent & Objective */}
        <div className="bg-navy-950/70 border border-navy-800/90 rounded-xl p-3.5">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Objective & Intent
          </div>
          <div className="text-xs font-medium text-slate-200">
            {understanding.primary_objective || understanding.intent}
          </div>
          <div className="mt-2">
            <Badge variant="neutral" className="text-[10px] px-2 py-0.5">
              Intent: {understanding.intent}
            </Badge>
          </div>
        </div>

        {/* Resolved Entities */}
        <div className="bg-navy-950/70 border border-navy-800/90 rounded-xl p-3.5">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Target Entities & Job
          </div>
          {understanding.resolved_entities.length > 0 ? (
            <div className="space-y-1.5">
              {understanding.resolved_entities.map((ent, idx) => (
                <div key={idx} className="flex items-center gap-1.5 text-xs text-slate-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                  <span className="font-medium text-slate-300">{ent.name}:</span>
                  <span className="text-slate-100 truncate">{ent.value}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-slate-400">All staged enterprise documents</div>
          )}
        </div>

        {/* Security & Constraints */}
        <div className="bg-navy-950/70 border border-navy-800/90 rounded-xl p-3.5">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Security & Constraints
          </div>
          <div className="space-y-1 text-xs">
            <div className="flex items-center gap-1.5 text-emerald-400">
              <Check className="w-3.5 h-3.5" />
              <span>Prompt injection & threat scan</span>
            </div>
            <div className="flex items-center gap-1.5 text-emerald-400">
              <Check className="w-3.5 h-3.5" />
              <span>Exclude high-risk candidates</span>
            </div>
            {understanding.required_conditions.map((cond, idx) => (
              <div key={idx} className="flex items-center gap-1.5 text-blue-300">
                <Check className="w-3.5 h-3.5" />
                <span>{cond.description}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Clarification Section (if ambiguity detected) */}
      {understanding.detected_ambiguities.length > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 mt-4">
          <div className="flex items-start gap-2.5">
            <HelpCircle className="w-4 h-4 text-amber-400 mt-0.5" />
            <div className="flex-1">
              <div className="text-xs font-semibold text-amber-300">
                Clarification Needed
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                {understanding.detected_ambiguities.join(' ')}
              </p>

              {understanding.clarification_questions.length > 0 && (
                <div className="flex flex-wrap items-center gap-2 mt-3">
                  {understanding.clarification_questions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => onSelectClarification?.(q, q)}
                      className="text-xs bg-navy-900 hover:bg-navy-800 border border-amber-500/40 hover:border-amber-400 text-slate-200 px-3 py-1.5 rounded-lg transition-all"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
