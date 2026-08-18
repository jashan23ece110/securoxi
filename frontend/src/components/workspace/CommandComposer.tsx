import React, { useState, useRef } from 'react';
import { Button, Badge } from '../ui';
import {
  Sparkles,
  Paperclip,
  FolderPlus,
  FileText,
  Link2,
  ArrowRight,
  ShieldCheck,
  Filter,
  Layers,
} from 'lucide-react';

interface CommandComposerProps {
  onRunTask: (prompt: string, options?: { mode?: string; constraints?: string[] }) => void;
  isLoading?: boolean;
  onAttachFiles?: () => void;
  onSelectFolder?: () => void;
  onAttachJD?: () => void;
  onConnectATS?: () => void;
  attachedCounts?: {
    files: number;
    folder?: string;
    jd?: string;
    atsConnected?: boolean;
  };
}

export const CommandComposer: React.FC<CommandComposerProps> = ({
  onRunTask,
  isLoading = false,
  onAttachFiles,
  onSelectFolder,
  onAttachJD,
  onConnectATS,
  attachedCounts,
}) => {
  const [prompt, setPrompt] = useState('');
  const [selectedConditions, setSelectedConditions] = useState<string[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const quickConditions = [
    { label: '+ Exclude High Risk', value: 'Exclude high-risk documents' },
    { label: '+ Minimum 5+ Years', value: 'Only candidates with 5+ years experience' },
    { label: '+ Required Kubernetes', value: 'Require production Kubernetes experience' },
    { label: '+ Top 20 Shortlist', value: 'Limit output to top 20 candidates' },
  ];

  const toggleCondition = (val: string) => {
    if (selectedConditions.includes(val)) {
      setSelectedConditions(selectedConditions.filter((c) => c !== val));
    } else {
      setSelectedConditions([...selectedConditions, val]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;
    onRunTask(prompt, { constraints: selectedConditions });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  return (
    <div className="w-full bg-navy-900 border border-navy-700/80 rounded-2xl p-6 shadow-2xl backdrop-blur-md">
      {/* Header Banner */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white tracking-wide">
              Intelligent Task Command Center
            </h2>
            <p className="text-xs text-slate-400">
              Tell SECUROXI what you need. AI evaluates security, verifies evidence, and synthesizes grounded answers.
            </p>
          </div>
        </div>
        <Badge variant="info" className="flex items-center gap-1.5 py-1 px-2.5">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-[11px] font-medium text-slate-300">Security Gate Active</span>
        </Badge>
      </div>

      {/* Main Textarea Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <textarea
            ref={textareaRef}
            rows={4}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="What would you like me to do? (e.g. Scan these resumes for prompt injection, compare them with this JD, and give me the top 20 safe candidates...)"
            className="w-full bg-navy-950/80 border border-navy-700/90 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all resize-y min-h-[100px]"
          />
          <div className="absolute right-3 bottom-3 text-[11px] text-slate-500">
            Press <kbd className="px-1.5 py-0.5 bg-navy-800 border border-navy-700 rounded text-slate-400">⌘+Enter</kbd> to run
          </div>
        </div>

        {/* Input Attachments Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-navy-800/80">
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={onAttachFiles}
              className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-navy-800/60 hover:bg-navy-800 border border-navy-700/60 hover:border-navy-600 px-3 py-1.5 rounded-lg transition-all"
            >
              <Paperclip className="w-3.5 h-3.5 text-blue-400" />
              <span>Attach Files</span>
              {attachedCounts?.files ? (
                <span className="ml-1 px-1.5 py-0.2 bg-blue-500/20 text-blue-400 rounded-full text-[10px]">
                  {attachedCounts.files}
                </span>
              ) : null}
            </button>

            <button
              type="button"
              onClick={onSelectFolder}
              className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-navy-800/60 hover:bg-navy-800 border border-navy-700/60 hover:border-navy-600 px-3 py-1.5 rounded-lg transition-all"
            >
              <FolderPlus className="w-3.5 h-3.5 text-amber-400" />
              <span>Select Folder</span>
              {attachedCounts?.folder ? (
                <span className="ml-1 px-1.5 py-0.2 bg-amber-500/20 text-amber-400 rounded-full text-[10px] truncate max-w-[100px]">
                  {attachedCounts.folder}
                </span>
              ) : null}
            </button>

            <button
              type="button"
              onClick={onAttachJD}
              className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-navy-800/60 hover:bg-navy-800 border border-navy-700/60 hover:border-navy-600 px-3 py-1.5 rounded-lg transition-all"
            >
              <FileText className="w-3.5 h-3.5 text-emerald-400" />
              <span>Attach Job Description</span>
              {attachedCounts?.jd ? (
                <span className="ml-1 px-1.5 py-0.2 bg-emerald-500/20 text-emerald-400 rounded-full text-[10px] truncate max-w-[100px]">
                  {attachedCounts.jd}
                </span>
              ) : null}
            </button>

            <button
              type="button"
              onClick={onConnectATS}
              className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-navy-800/60 hover:bg-navy-800 border border-navy-700/60 hover:border-navy-600 px-3 py-1.5 rounded-lg transition-all"
            >
              <Link2 className="w-3.5 h-3.5 text-purple-400" />
              <span>Connect ATS (Optional)</span>
              {attachedCounts?.atsConnected ? (
                <span className="ml-1 px-1.5 py-0.2 bg-purple-500/20 text-purple-400 rounded-full text-[10px]">
                  Live
                </span>
              ) : null}
            </button>
          </div>

          <Button
            type="submit"
            disabled={!prompt.trim() || isLoading}
            isLoading={isLoading}
            variant="primary"
            className="flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-medium shadow-lg shadow-blue-500/20"
          >
            <span>Run Task</span>
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>

        {/* Quick Conditions Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-2">
          <span className="text-[11px] text-slate-500 flex items-center gap-1 mr-1">
            <Filter className="w-3 h-3" /> Quick filters:
          </span>
          {quickConditions.map((cond) => {
            const isSelected = selectedConditions.includes(cond.value);
            return (
              <button
                key={cond.label}
                type="button"
                onClick={() => toggleCondition(cond.value)}
                className={`text-[11px] px-2.5 py-1 rounded-full border transition-all ${
                  isSelected
                    ? 'bg-blue-500/20 text-blue-300 border-blue-500/40 font-medium'
                    : 'bg-navy-950/60 text-slate-400 border-navy-800 hover:border-navy-700 hover:text-slate-300'
                }`}
              >
                {cond.label}
              </button>
            );
          })}
        </div>
      </form>
    </div>
  );
};
