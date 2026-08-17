/**
 * Typed REST API Client consuming SECUROXI FastAPI Backend.
 */

import { ScanReport, Incident, AuditEvent, PolicyRule, ScreeningResult } from './types';

const API_BASE = '/api/v1';

export class SecuroxiApiClient {
  private apiKey: string;

  constructor(apiKey: string = 'securoxi_dev_secret_key_123') {
    this.apiKey = apiKey;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers = {
      'Content-Type': 'application/json',
      'X-API-Key': this.apiKey,
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
      },
      body: formData,
    });

    if (!res.ok) {
      throw new Error(`Upload failed: ${res.statusText}`);
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
}

export const api = new SecuroxiApiClient();
