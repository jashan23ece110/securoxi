import React from 'react';
import { Card, Badge } from '../ui';
import {
  FolderArchive,
  FileText,
  FileCheck,
  Link2,
  X,
  Layers,
  Database,
  Info,
} from 'lucide-react';

export interface AttachedInputContext {
  files: Array<{ name: string; size: string; status?: string }>;
  folder?: { name: string; totalFiles: number; supported: number };
  jobDescription?: { title: string; requiredSkills: string[]; expYears?: number; textSnippet?: string };
  atsConnection?: { system: string; connected: boolean; candidateCount?: number };
}

interface InputContextPanelProps {
  context: AttachedInputContext;
  onRemoveFiles?: () => void;
  onRemoveFolder?: () => void;
  onRemoveJD?: () => void;
  onRemoveATS?: () => void;
}

export const InputContextPanel: React.FC<InputContextPanelProps> = ({
  context,
  onRemoveFiles,
  onRemoveFolder,
  onRemoveJD,
  onRemoveATS,
}) => {
  const hasAnyContext =
    context.files.length > 0 ||
    !!context.folder ||
    !!context.jobDescription ||
    !!context.atsConnection?.connected;

  if (!hasAnyContext) {
    return null;
  }

  return (
    <div className="w-full bg-navy-900/60 border border-navy-800/80 rounded-xl p-4 my-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-400" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Attached Task Context
          </h3>
        </div>
        <span className="text-[11px] text-slate-500">Inputs will be verified before reasoning</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Attached Files */}
        {context.files.length > 0 && (
          <div className="bg-navy-950/70 border border-navy-800/90 rounded-lg p-3 relative group">
            <button
              onClick={onRemoveFiles}
              className="absolute top-2 right-2 text-slate-500 hover:text-red-400 transition-colors p-1"
              title="Remove files"
            >
              <X className="w-3.5 h-3.5" />
            </button>
            <div className="flex items-start gap-2.5">
              <div className="p-2 rounded-md bg-blue-500/10 text-blue-400 mt-0.5">
                <FileCheck className="w-4 h-4" />
              </div>
              <div className="min-w-0 pr-4">
                <div className="text-xs font-medium text-slate-200">Attached Documents</div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {context.files.length} document{context.files.length > 1 ? 's' : ''} staged
                </div>
                <div className="text-[10px] text-slate-500 truncate mt-1">
                  {context.files.map((f) => f.name).slice(0, 2).join(', ')}
                  {context.files.length > 2 ? ` +${context.files.length - 2} more` : ''}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Selected Folder */}
        {context.folder && (
          <div className="bg-navy-950/70 border border-navy-800/90 rounded-lg p-3 relative group">
            <button
              onClick={onRemoveFolder}
              className="absolute top-2 right-2 text-slate-500 hover:text-red-400 transition-colors p-1"
              title="Remove folder"
            >
              <X className="w-3.5 h-3.5" />
            </button>
            <div className="flex items-start gap-2.5">
              <div className="p-2 rounded-md bg-amber-500/10 text-amber-400 mt-0.5">
                <FolderArchive className="w-4 h-4" />
              </div>
              <div className="min-w-0 pr-4">
                <div className="text-xs font-medium text-slate-200 truncate">{context.folder.name}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {context.folder.totalFiles.toLocaleString()} files discovered
                </div>
                <div className="text-[10px] text-emerald-400 mt-1">
                  {context.folder.supported.toLocaleString()} supported formats
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Attached Job Description */}
        {context.jobDescription && (
          <div className="bg-navy-950/70 border border-navy-800/90 rounded-lg p-3 relative group">
            <button
              onClick={onRemoveJD}
              className="absolute top-2 right-2 text-slate-500 hover:text-red-400 transition-colors p-1"
              title="Remove Job Description"
            >
              <X className="w-3.5 h-3.5" />
            </button>
            <div className="flex items-start gap-2.5">
              <div className="p-2 rounded-md bg-emerald-500/10 text-emerald-400 mt-0.5">
                <FileText className="w-4 h-4" />
              </div>
              <div className="min-w-0 pr-4">
                <div className="text-xs font-medium text-slate-200 truncate">
                  {context.jobDescription.title || 'Job Description'}
                </div>
                {context.jobDescription.requiredSkills.length > 0 ? (
                  <div className="text-[11px] text-slate-400 mt-0.5 truncate">
                    Skills: {context.jobDescription.requiredSkills.slice(0, 3).join(', ')}
                  </div>
                ) : (
                  <div className="text-[11px] text-slate-400 mt-0.5">Standard criteria loaded</div>
                )}
                {context.jobDescription.expYears && (
                  <div className="text-[10px] text-blue-400 mt-1">
                    Req: {context.jobDescription.expYears}+ yrs
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ATS Connection */}
        {context.atsConnection?.connected && (
          <div className="bg-navy-950/70 border border-navy-800/90 rounded-lg p-3 relative group">
            <button
              onClick={onRemoveATS}
              className="absolute top-2 right-2 text-slate-500 hover:text-red-400 transition-colors p-1"
              title="Disconnect ATS"
            >
              <X className="w-3.5 h-3.5" />
            </button>
            <div className="flex items-start gap-2.5">
              <div className="p-2 rounded-md bg-purple-500/10 text-purple-400 mt-0.5">
                <Link2 className="w-4 h-4" />
              </div>
              <div className="min-w-0 pr-4">
                <div className="text-xs font-medium text-slate-200">
                  {context.atsConnection.system} ATS
                </div>
                <div className="text-[11px] text-emerald-400 mt-0.5">Connected (Live)</div>
                {context.atsConnection.candidateCount && (
                  <div className="text-[10px] text-slate-400 mt-1">
                    {context.atsConnection.candidateCount} sync candidates
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
