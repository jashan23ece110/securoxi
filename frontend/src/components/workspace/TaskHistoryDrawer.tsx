import React from 'react';
import { Drawer, Badge, Button } from '../ui';
import { History, Clock, CheckCircle2, AlertCircle, ArrowRight, RotateCcw } from 'lucide-react';

interface TaskHistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  tasks: Array<{
    task_id: string;
    task_description: string;
    status: string;
    created_at: string | number;
  }>;
  onSelectTask: (taskId: string) => void;
}

export const TaskHistoryDrawer: React.FC<TaskHistoryDrawerProps> = ({
  isOpen,
  onClose,
  tasks,
  onSelectTask,
}) => {
  return (
    <Drawer isOpen={isOpen} onClose={onClose} title="Recent Agentic Tasks" maxWidth="480px">
      <div className="space-y-4 p-4">
        <p className="text-xs text-slate-400">
          Restore authorized task context and inspect previous execution outcomes.
        </p>

        {tasks.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs">
            No previous tasks found for this workspace.
          </div>
        ) : (
          <div className="space-y-2.5">
            {tasks.map((task) => (
              <div
                key={task.task_id}
                onClick={() => onSelectTask(task.task_id)}
                className="p-3.5 rounded-xl bg-navy-900 hover:bg-navy-850 border border-navy-700/80 hover:border-blue-500/50 cursor-pointer transition-all space-y-2 group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono text-slate-400">{task.task_id}</span>
                  <Badge
                    variant={task.status === 'COMPLETED' ? 'safe' : 'neutral'}
                    className="text-[10px] px-2 py-0.5"
                  >
                    {task.status}
                  </Badge>
                </div>

                <div className="text-xs font-medium text-slate-200 group-hover:text-blue-300 transition-colors line-clamp-2">
                  {task.task_description}
                </div>

                <div className="flex items-center justify-between pt-1 text-[11px] text-slate-500">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {typeof task.created_at === 'number'
                      ? new Date(task.created_at * 1000).toLocaleTimeString()
                      : task.created_at}
                  </span>
                  <span className="text-blue-400 group-hover:translate-x-0.5 transition-transform flex items-center gap-0.5 font-medium">
                    <span>Load</span>
                    <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Drawer>
  );
};
