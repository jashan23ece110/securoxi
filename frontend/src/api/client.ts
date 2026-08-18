/**
 * Typed REST API Client consuming SECUROXI FastAPI Backend.
 */

import { ScanReport, Incident, AuditEvent, PolicyRule, ScreeningResult, RAGAnswer } from './types';

const API_BASE = '/api/v1';

export class SecuroxiApiClient {
  private apiKey: string;
  private tenantId: string;

  constructor(
    apiKey?: string,
    tenantId?: string
  ) {
    this.apiKey =
      apiKey ||
      (typeof window !== 'undefined' && localStorage.getItem('securoxi_api_key')) ||
      (import.meta as any).env?.VITE_SECUROXI_API_KEY ||
      'securoxi-enterprise-key';
    this.tenantId =
      tenantId ||
      (typeof window !== 'undefined' && localStorage.getItem('securoxi_tenant_id')) ||
      'TENANT-DEFAULT';
  }

  setApiKey(key: string) {
    this.apiKey = key;
    if (typeof window !== 'undefined') {
      localStorage.setItem('securoxi_api_key', key);
    }
  }

  setTenantId(tenantId: string) {
    this.tenantId = tenantId;
    if (typeof window !== 'undefined') {
      localStorage.setItem('securoxi_tenant_id', tenantId);
    }
  }

  getApiKey(): string {
    return this.apiKey;
  }

  getTenantId(): string {
    return this.tenantId;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers = {
      'Content-Type': 'application/json',
      'X-API-Key': this.apiKey,
      'X-Tenant-ID': this.tenantId,
      ...options.headers,
    };

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: 'API request failed' }));
      throw new Error(errData.detail || `HTTP ${res.status}: ${res.statusText}`);
    }

    return res.json();
  }

  // Scans & Analysis
  async listScans(): Promise<ScanReport[]> {
    return this.request<ScanReport[]>('/scans');
  }

  async getScan(scanId: string): Promise<ScanReport> {
    return this.request<ScanReport>(`/scan/${scanId}`);
  }

  async exportScans(format: 'csv' | 'json' = 'csv', verdict?: string): Promise<Blob> {
    const params = new URLSearchParams({ format });
    if (verdict && verdict !== 'ALL') params.append('verdict', verdict);

    const res = await fetch(`${API_BASE}/scans/export?${params.toString()}`, {
      headers: {
        'X-API-Key': this.apiKey,
        'X-Tenant-ID': this.tenantId,
      },
    });

    if (!res.ok) {
      throw new Error(`Export failed: ${res.statusText}`);
    }

    return res.blob();
  }

  async uploadAndScanDocument(file: File): Promise<ScanReport> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/scan`, {
      method: 'POST',
      headers: {
        'X-API-Key': this.apiKey,
        'X-Tenant-ID': this.tenantId,
      },
      body: formData,
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: `Upload failed: ${res.statusText}` }));
      throw new Error(errData.detail || `Upload failed: ${res.statusText}`);
    }

    return res.json();
  }

  // Incidents
  async listIncidents(): Promise<Incident[]> {
    return this.request<Incident[]>('/brain/incidents');
  }

  async resolveIncident(incidentId: string, resolutionNotes?: string): Promise<{ status: string }> {
    return this.request<{ status: string }>(`/brain/incidents/${incidentId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution_notes: resolutionNotes }),
    }).catch(() => ({ status: 'RESOLVED' }));
  }

  // Audit Logs
  async listAuditLogs(): Promise<AuditEvent[]> {
    return this.request<AuditEvent[]>('/audit-logs');
  }

  // Policy Rules
  async listPolicies(): Promise<PolicyRule[]> {
    return this.request<PolicyRule[]>('/policies');
  }

  // Screening
  async listScreenings(): Promise<ScreeningResult[]> {
    return this.request<ScreeningResult[]>('/screening/results');
  }

  // System Health
  async getSystemHealth(): Promise<Record<string, any>> {
    return this.request<Record<string, any>>('/health');
  }

  async bulkScanFiles(files: File[]): Promise<{
    total_files: number;
    safe: number;
    suspicious: number;
    high_risk: number;
    uninspectable?: number;
    results: ScanReport[];
  }> {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const res = await fetch(`${API_BASE}/scan/bulk`, {
      method: 'POST',
      headers: {
        'X-API-Key': this.apiKey,
        'X-Tenant-ID': this.tenantId,
      },
      body: formData,
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: `Bulk upload failed: ${res.statusText}` }));
      throw new Error(errData.detail || `Bulk upload failed: ${res.statusText}`);
    }

    return res.json();
  }

  // Batch Jobs
  async getBatchStatus(batchId: string): Promise<any> {
    return this.request<any>(`/batches/${batchId}`);
  }

  async retryBatch(batchId: string): Promise<any> {
    return this.request<any>(`/batches/${batchId}/retry`, { method: 'POST' });
  }

  async cancelBatch(batchId: string): Promise<any> {
    return this.request<any>(`/batches/${batchId}/cancel`, { method: 'POST' });
  }

  // Grounded RAG & Question Answering
  async askSecuroxi(query: string, topK: number = 4): Promise<RAGAnswer> {
    return this.request<RAGAnswer>('/ask', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK }),
    });
  }

  // Intelligence 2.0 Agentic RAG & Unified Command Workspace (Phase 4)
  async understandTask(prompt: string, context?: any): Promise<import('./types').TaskUnderstandingPreview> {
    return this.request<import('./types').TaskUnderstandingPreview>('/agentic/understand', {
      method: 'POST',
      body: JSON.stringify({ prompt, context }),
    });
  }

  async executeAgenticTask(payload: {
    task_description: string;
    synthesis_mode?: string;
    comparison_entities?: any[];
    retrieval_chunks?: any[];
    security_clearance?: string;
    allow_untrusted?: boolean;
    context?: any;
  }): Promise<import('./types').AgenticExecutionResult> {
    return this.request<import('./types').AgenticExecutionResult>('/agentic/execute', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listAgenticTasks(limit: number = 20): Promise<any[]> {
    return this.request<any[]>(`/agentic/tasks?limit=${limit}`);
  }

  // Autonomous Task Execution (Stage 18)
  async submitAutonomousTask(payload: {
    objective: string;
    context?: any;
    constraints?: string[];
    source_restrictions?: string[];
    synthesis_mode?: string;
    comparison_entities?: any[];
    retrieval_chunks?: any[];
  }): Promise<{ task_id: string; run_id: string; tenant_id: string; status: string; context_id: string }> {
    return this.request<{ task_id: string; run_id: string; tenant_id: string; status: string; context_id: string }>(
      '/agentic/task/submit',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  }

  async getTaskStatus(taskId: string): Promise<any> {
    return this.request<any>(`/agentic/task/${taskId}/status`);
  }

  async pauseTask(taskId: string): Promise<{ status: string; task_id: string }> {
    return this.request<{ status: string; task_id: string }>(`/agentic/task/${taskId}/pause`, {
      method: 'POST',
    });
  }

  async resumeTask(taskId: string): Promise<{ status: string; task_id: string }> {
    return this.request<{ status: string; task_id: string }>(`/agentic/task/${taskId}/resume`, {
      method: 'POST',
    });
  }

  async cancelTask(taskId: string): Promise<{ status: string; task_id: string }> {
    return this.request<{ status: string; task_id: string }>(`/agentic/task/${taskId}/cancel`, {
      method: 'POST',
    });
  }

  async decideTaskApproval(
    taskId: string,
    approvalId: string,
    approved: boolean,
    reason?: string
  ): Promise<{ status: string; task_id: string }> {
    return this.request<{ status: string; task_id: string }>(`/agentic/task/${taskId}/approval/decide`, {
      method: 'POST',
      body: JSON.stringify({ approval_id: approvalId, approved, reason }),
    });
  }

  // Intelligent Hiring Workspace (Stage 19)
  async screenHiringCandidates(payload: {
    task_description?: string;
    job_description?: any;
    candidates?: any[];
    context?: any;
    constraints?: string[];
    target_shortlist_count?: number;
  }): Promise<any> {
    return this.request<any>('/agentic/hiring/screen', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async compareHiringCandidates(payload: {
    candidate_ids: string[];
    all_candidates: any[];
    role_title?: string;
  }): Promise<any> {
    return this.request<any>('/agentic/hiring/compare', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async advanceAtsCandidate(payload: {
    candidate_id: string;
    candidate_name: string;
    security_status: string;
    target_stage?: string;
  }): Promise<{ status: string; task_id: string; approval_id: string; action_summary: string; candidate_id: string }> {
    return this.request<{ status: string; task_id: string; approval_id: string; action_summary: string; candidate_id: string }>(
      '/agentic/hiring/ats/advance',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  }

  // Agentic RAG / Ask SECUROXI (Stage 20)
  async askAgenticSecuroxi(payload: {
    query: string;
    scope?: string;
    context?: any;
    mode?: string;
    retrieval_chunks?: any[];
  }): Promise<any> {
    return this.request<any>('/agentic/ask', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Security Investigation & Evidence Workspace (Stage 21)
  async createInvestigation(payload: {
    subject: string;
    document_id?: string;
    candidate_id?: string;
    finding_type?: string;
    security_status?: string;
    severity?: string;
    evidence?: string;
    metadata?: any;
  }): Promise<any> {
    return this.request<any>('/agentic/investigation/create', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getInvestigation(investigationId: string): Promise<any> {
    return this.request<any>(`/agentic/investigation/${investigationId}`);
  }

  async addInvestigationNote(investigationId: string, text: string, author?: string): Promise<any> {
    return this.request<any>(`/agentic/investigation/${investigationId}/note`, {
      method: 'POST',
      body: JSON.stringify({ text, author }),
    });
  }

  async requestInvestigationAction(investigationId: string, actionType: string, reason: string): Promise<any> {
    return this.request<any>(`/agentic/investigation/${investigationId}/action`, {
      method: 'POST',
      body: JSON.stringify({ action_type: actionType, reason }),
    });
  }

  async askInvestigationQuestion(investigationId: string, query: string, expandScope: boolean = false): Promise<any> {
    return this.request<any>(`/agentic/investigation/${investigationId}/ask`, {
      method: 'POST',
      body: JSON.stringify({ query, expand_scope: expandScope }),
    });
  }

  async exportInvestigationReport(investigationId: string): Promise<any> {
    return this.request<any>(`/agentic/investigation/${investigationId}/export`);
  }

  // Unified Live Task & Security Monitoring Workspace (Stage 22)
  async getMonitoringOverview(): Promise<any> {
    return this.request<any>('/agentic/monitoring/overview');
  }

  async getMonitoringEvents(category?: string, limit: number = 50): Promise<any> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    params.append('limit', String(limit));
    return this.request<any>(`/agentic/monitoring/events?${params.toString()}`);
  }

  async getMonitoringTelemetry(): Promise<any> {
    return this.request<any>('/agentic/monitoring/telemetry');
  }

  // Human Approval, Governance & Controlled Action Workspace (Stage 23)
  async createGovernanceProposal(payload: {
    task_id?: string;
    requester?: string;
    action_type: string;
    targets: any[];
    reason: string;
    impact_level?: string;
    policy_ref?: string;
    security_state?: string;
    evidence_refs?: string[];
  }): Promise<any> {
    return this.request<any>('/agentic/governance/proposals', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listGovernanceProposals(status?: string): Promise<any[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    return this.request<any[]>(`/agentic/governance/proposals?${params.toString()}`);
  }

  async getGovernanceProposal(proposalId: string): Promise<any> {
    return this.request<any>(`/agentic/governance/proposals/${proposalId}`);
  }

  async decideGovernanceProposal(proposalId: string, approved: boolean, deciderId?: string, comment?: string): Promise<any> {
    return this.request<any>(`/agentic/governance/proposals/${proposalId}/decide`, {
      method: 'POST',
      body: JSON.stringify({ approved, decider_id: deciderId, comment }),
    });
  }

  async executeGovernanceProposal(proposalId: string, actorId?: string): Promise<any> {
    return this.request<any>(`/agentic/governance/proposals/${proposalId}/execute`, {
      method: 'POST',
      body: JSON.stringify({ actor_id: actorId }),
    });
  }

  async getGovernanceAudit(limit: number = 50): Promise<any[]> {
    return this.request<any[]>(`/agentic/governance/audit?limit=${limit}`);
  }
}

export const api = new SecuroxiApiClient();
