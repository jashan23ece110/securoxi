/**
 * SECUROXI Backend Typed Interfaces
 * Matches backend Pydantic & database schemas.
 */

export type Verdict = 'SAFE' | 'SUSPICIOUS' | 'HIGH_RISK' | 'CRITICAL' | 'BLOCKED';

export interface SecurityFinding {
  threat_type: string;
  category: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number;
  description: string;
  evidence: string;
  line_number?: number;
  pattern_matched?: string;
}

export interface ScanReport {
  scan_id: string;
  filename: string;
  document_type: string;
  verdict: Verdict;
  risk_score: number;
  findings: SecurityFinding[];
  summary: string;
  created_at: string;
  tenant_id: string;
}

export interface Incident {
  incident_id: string;
  source: string;
  affected_asset: string;
  attack_type: string;
  severity: string;
  risk_score: number;
  status: 'DETECTED' | 'TRIAGED' | 'INVESTIGATING' | 'RESPONDED' | 'RESOLVED' | 'CLOSED';
  evidence: string;
  policy_decision: {
    action: string;
    rule_name: string;
  };
  response_actions: string[];
  created_at: string;
}

export interface CandidateProfile {
  candidate_id: string;
  name: string;
  email: string;
  phone: string;
  skills: string[];
  total_years_exp: number;
  parsed_resume_text: string;
  security_verdict: Verdict;
}

export interface ScreeningResult {
  screening_id: string;
  candidate_id: string;
  job_id: string;
  fit_score: number;
  skill_match_pct: number;
  qualification_verdict: string;
  explanation: string;
  security_clearance: boolean;
}

export interface AuditEvent {
  log_id: number;
  timestamp: string;
  event_type: string;
  user_id: string;
  tenant_id: string;
  details: string;
}

export interface PolicyRule {
  rule_id: string;
  rule_name: string;
  priority: number;
  action: string;
  condition: string;
}

export interface Tenant {
  tenant_id: string;
  name: string;
  created_at: string;
  status: string;
}

export interface RAGCitation {
  citation_id: number;
  document_id: string;
  page: number;
  section?: string;
  similarity_score: number;
}

export interface RAGAnswer {
  query: string;
  tenant_id: string;
  answer_text: string;
  citations: RAGCitation[];
  confidence_score: number;
  groundedness_score: number;
  retrieved_chunks_count: number;
  execution_time_ms: number;
  is_grounded: boolean;
}

export interface TaskUnderstandingPreview {
  intent: string;
  primary_objective: string;
  resolved_entities: Array<{ entity_type: string; name: string; value: string }>;
  required_conditions: Array<{ condition_type: string; description: string; is_mandatory: boolean }>;
  priority_hierarchy?: string[];
  detected_ambiguities: string[];
  clarification_questions: string[];
}

export interface AgenticExecutionResult {
  task_id: string;
  tenant_id: string;
  status: string;
  groundedness_state: string;
  answer_status: string;
  executive_summary: string;
  detailed_answer: string;
  derived_claims: Array<{
    derived_claim_id: string;
    text: string;
    source_claim_ids: string[];
    derivation_rationale: string;
    is_reverified: boolean;
    confidence: number;
  }>;
  comparisons: Array<{
    dimension: string;
    entity_a_value: string;
    entity_b_value: string;
    comparison_verdict: string;
  }>;
  recommendations: string[];
  citations: Array<{
    citation_id: string;
    document_id: string;
    chunk_id: string;
    source: string;
    snippet: string;
  }>;
  conflicts: any[];
  collected_chunks_count: number;
  hops_executed: number;
}
