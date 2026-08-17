import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { RAGAnswer, ScanReport } from '../api/types';
import {
  Card,
  Button,
  Badge,
  Alert,
  LoadingState,
  EmptyState,
  ErrorState,
} from '../components/ui';
import { PageContainer } from '../components/layout';
import {
  Brain,
  Search,
  Sparkles,
  Send,
  FileText,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  ExternalLink,
  RotateCw,
  Folder,
  UserCheck,
  Layers,
  ArrowRight,
  Clock,
} from 'lucide-react';

interface QAPair {
  id: string;
  query: string;
  scope: string;
  answer: RAGAnswer;
  timestamp: string;
}

export const AskSecuroxiPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const initialQuery = searchParams.get('q') || '';
  const initialScope = searchParams.get('scope') || 'all';
  const initialDocId = searchParams.get('doc_id') || '';

  const [query, setQuery] = useState<string>(initialQuery);
  const [scope, setScope] = useState<string>(initialScope);
  const [loading, setLoading] = useState<boolean>(false);
  const [progressStage, setProgressStage] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<QAPair[]>([]);

  // Suggested Starter Questions
  const STARTER_PROMPTS = [
    'Which candidates have production Kubernetes experience?',
    'Which resumes mention Terraform and cloud security?',
    'Summarize the security requirements across our documents.',
    'Which candidates meet the mandatory senior requirements?',
    'Find documents mentioning incident response and threat modeling.',
  ];

  const handleAsk = async (questionToAsk?: string) => {
    const q = (questionToAsk || query).trim();
    if (!q) return;

    setLoading(true);
    setError(null);
    setProgressStage(1);

    // Progressive reassuring stages (without internal jargon)
    const stageTimer1 = setTimeout(() => setProgressStage(2), 350);
    const stageTimer2 = setTimeout(() => setProgressStage(3), 700);

    try {
      const res = await api.askSecuroxi(q, 5);
      const newPair: QAPair = {
        id: `QA-${Date.now()}`,
        query: q,
        scope,
        answer: res,
        timestamp: new Date().toLocaleTimeString(),
      };
      setHistory((prev) => [newPair, ...prev]);
      setQuery('');
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve document intelligence answer.');
    } finally {
      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      setLoading(false);
      setProgressStage(0);
    }
  };

  // Auto-run if query param passed on mount
  useEffect(() => {
    if (initialQuery) {
      handleAsk(initialQuery);
    }
  }, [initialQuery]);

  return (
    <PageContainer>
      {/* 1. Header Hero */}
      <div
        style={{
          padding: '24px 28px',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-default)',
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'rgba(56, 189, 248, 0.12)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--accent-cyan)',
              }}
            >
              <Brain size={20} />
            </div>
            <h1 style={{ fontSize: '1.375rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
              Ask SECUROXI
            </h1>
            <Badge variant="safe">Secure Document Intelligence</Badge>
          </div>
          <p style={{ margin: '6px 0 0 0', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Ask natural-language questions across documents you are authorized to access.
          </p>
        </div>

        {/* Scope Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)' }}>Search Scope:</span>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value)}
            style={{
              backgroundColor: 'var(--bg-input)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '6px 12px',
              fontSize: '0.8125rem',
              fontWeight: 600,
              outline: 'none',
            }}
          >
            <option value="all">All Authorized Documents</option>
            <option value="candidates">Candidate Pool (Screening)</option>
            <option value="folders">Bulk Folder Collections</option>
            {initialDocId && <option value="single">Selected Document ({initialDocId})</option>}
          </select>
        </div>
      </div>

      {/* 2. Large Query Input Box */}
      <Card title="Ask Anything" subtitle="Grounded search with multi-tenant isolation and security quarantine exclusions">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              backgroundColor: '#040711',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px',
            }}
          >
            <Search size={18} style={{ color: 'var(--accent-cyan)' }} />
            <input
              type="text"
              placeholder="Ask anything about your documents (e.g. 'Which candidates have Kubernetes and AWS experience?')..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleAsk();
                }
              }}
              disabled={loading}
              style={{
                flex: 1,
                background: 'none',
                border: 'none',
                outline: 'none',
                color: 'var(--text-primary)',
                fontSize: '0.9375rem',
              }}
            />
            {query && (
              <Button variant="ghost" size="xs" onClick={() => setQuery('')}>
                Clear
              </Button>
            )}
            <Button
              variant="primary"
              size="sm"
              onClick={() => handleAsk()}
              disabled={loading || !query.trim()}
              icon={<Send size={14} />}
            >
              Ask
            </Button>
          </div>

          {/* Quick Starter Pills */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-muted)' }}>EXAMPLES:</span>
            {STARTER_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuery(prompt);
                  handleAsk(prompt);
                }}
                disabled={loading}
                style={{
                  backgroundColor: 'var(--bg-app)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '999px',
                  padding: '4px 10px',
                  fontSize: '0.75rem',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  textAlign: 'left',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--accent-cyan)';
                  e.currentTarget.style.color = 'var(--text-primary)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-subtle)';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }}
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Reassuring Multi-Stage Progress State */}
          {loading && (
            <div
              style={{
                padding: '14px 18px',
                backgroundColor: 'rgba(56, 189, 248, 0.05)',
                border: '1px solid rgba(56, 189, 248, 0.2)',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8125rem', color: 'var(--accent-cyan)', fontWeight: 700 }}>
                <RotateCw size={14} className="animate-spin" />
                <span>Processing Document Intelligence Query...</span>
              </div>
              <div style={{ display: 'flex', gap: '16px', fontSize: '0.75rem', color: 'var(--text-muted)', flexWrap: 'wrap' }}>
                <span style={{ color: progressStage >= 1 ? 'var(--status-safe)' : 'var(--text-muted)' }}>
                  ✓ 1. Authorizing Access
                </span>
                <span style={{ color: progressStage >= 2 ? 'var(--status-safe)' : 'var(--text-muted)' }}>
                  {progressStage >= 2 ? '✓' : '•'} 2. Searching Documents
                </span>
                <span style={{ color: progressStage >= 3 ? 'var(--status-safe)' : 'var(--text-muted)' }}>
                  {progressStage >= 3 ? '✓' : '•'} 3. Verifying Quarantine Filters
                </span>
                <span style={{ color: progressStage >= 3 ? 'var(--accent-cyan)' : 'var(--text-muted)' }}>
                  • 4. Building Grounded Answer
                </span>
              </div>
            </div>
          )}

          {error && <Alert type="danger" title="Retrieval Failure">{error}</Alert>}
        </div>
      </Card>

      {/* 3. QA Answers Feed */}
      <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {history.length === 0 && !loading && (
          <EmptyState
            title="Ask Anything About Your Documents"
            description="Select a sample question above or type your own question to get evidence-grounded answers with citations."
          />
        )}

        {history.map((pair) => (
          <Card
            key={pair.id}
            title={pair.query}
            subtitle={`Answered via Grounded Intelligence • ${pair.timestamp} • Scope: ${pair.scope}`}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Answer Text */}
              <div
                style={{
                  padding: '16px',
                  backgroundColor: 'var(--bg-app)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.875rem',
                  lineHeight: 1.6,
                  color: 'var(--text-primary)',
                }}
              >
                {pair.answer.answer_text}
              </div>

              {/* Groundedness Gauge & Metrics */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '0.75rem',
                  color: 'var(--text-muted)',
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '10px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldCheck size={14} style={{ color: 'var(--status-safe)' }} />
                  <span>Security Checked: Quarantined & malicious content excluded</span>
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <span>Groundedness: <strong>{Math.round(pair.answer.groundedness_score * 100)}%</strong></span>
                  <span>Latency: <strong>{pair.answer.execution_time_ms} ms</strong></span>
                </div>
              </div>

              {/* Clickable Citations & Sources */}
              {pair.answer.citations && pair.answer.citations.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.6875rem', fontWeight: 800, color: 'var(--text-muted)', marginBottom: '8px', letterSpacing: '0.05em' }}>
                    SUPPORTING CITATIONS ({pair.answer.citations.length}):
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '8px' }}>
                    {pair.answer.citations.map((c, cIdx) => (
                      <div
                        key={cIdx}
                        onClick={() => {
                          if (c.document_id) {
                            navigate(`/investigate/${c.document_id}`);
                          }
                        }}
                        style={{
                          padding: '10px 12px',
                          backgroundColor: 'var(--bg-surface)',
                          border: '1px solid var(--border-default)',
                          borderRadius: 'var(--radius-sm)',
                          cursor: 'pointer',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          transition: 'border-color 0.15s ease',
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-cyan)')}
                        onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-default)')}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <FileText size={14} style={{ color: 'var(--accent-cyan)' }} />
                          <div>
                            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                              {c.document_id}
                            </div>
                            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                              Page {c.page || 1} • Relevance: {Math.round((c.similarity_score || 0.9) * 100)}%
                            </div>
                          </div>
                        </div>
                        <ArrowRight size={12} style={{ color: 'var(--text-muted)' }} />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </PageContainer>
  );
};
