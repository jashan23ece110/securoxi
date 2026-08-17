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
}

export const api = new SecuroxiApiClient();
