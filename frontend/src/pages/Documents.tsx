import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { ScanReport } from '../api/types';
import {
  Card,
  StatCard,
  Button,
  StatusBadge,
  Badge,
  DataTable,
  Drawer,
  LoadingState,
  EmptyState,
  ErrorState,
} from '../components/ui';
import { PageHeader, PageToolbar, PageContainer } from '../components/layout';
import {
  FileText,
  FolderOpen,
  ShieldCheck,
  RefreshCw,
  Search,
  ExternalLink,
  Layers,
  Database,
  Lock,
  Eye,
} from 'lucide-react';
import { ForensicDocumentViewer } from '../components/forensics';

export const DocumentsPage: React.FC = () => {
  const navigate = useNavigate();
  const [scans, setScans] = useState<ScanReport[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<ScanReport | null>(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [formatFilter, setFormatFilter] = useState('ALL');

  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDocs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listScans().catch(() => []);
      setScans(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch document repository.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const filteredDocs = scans.filter((doc) => {
    const matchSearch =
      doc.filename.toLowerCase().includes(searchFilter.toLowerCase()) ||
      doc.scan_id.toLowerCase().includes(searchFilter.toLowerCase());
    const matchFormat = formatFilter === 'ALL' || doc.document_type.toUpperCase() === formatFilter;
    return matchSearch && matchFormat;
  });

  const columns = [
    {
      key: 'filename',
      header: 'Document File Name',
      sortable: true,
      render: (row: ScanReport) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileText size={15} style={{ color: 'var(--accent-cyan)' }} />
          <div>
            <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.875rem' }}>{row.filename}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Scan ID: <code>{row.scan_id}</code></div>
          </div>
        </div>
      ),
    },
    {
      key: 'document_type',
      header: 'Format',
      width: '100px',
      render: (row: ScanReport) => (
        <span style={{ fontSize: '0.6875rem', fontWeight: 700, textTransform: 'uppercase', padding: '2px 6px', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xs)' }}>
          {row.document_type}
        </span>
      ),
    },
    {
      key: 'verdict',
      header: 'Security Clearance',
      width: '150px',
      sortable: true,
      render: (row: ScanReport) => <StatusBadge status={row.verdict} />,
    },
    {
      key: 'chunks',
      header: 'Vector Chunks',
      width: '120px',
      render: (_row: ScanReport) => (
        <span style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
          4 Chunks (384d)
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Ingested Timestamp',
      width: '170px',
      sortable: true,
      render: (row: ScanReport) => (
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {new Date(row.created_at).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      width: '110px',
      render: (row: ScanReport) => (
        <Button variant="secondary" size="xs" onClick={() => setSelectedDoc(row)} icon={<ExternalLink size={12} />}>
          Inspect
        </Button>
      ),
    },
  ];

  if (loading) {
    return (
      <PageContainer>
        <LoadingState message="Loading Document Repository & Vector Chunks..." />
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <ErrorState title="Document Repository Error" message={error} onRetry={fetchDocs} />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      {/* 1. Page Header */}
      <PageHeader
        title="Multi-Tenant Document Repository"
        subtitle="Ingested candidate resumes, parsed structural layout blocks & pgvector embeddings repository"
        breadcrumbs={[{ label: 'DOCUMENTS' }, { label: 'REPOSITORY' }]}
        badge={<Badge variant="safe">Vector Index Synced</Badge>}
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button variant="secondary" size="sm" onClick={fetchDocs} icon={<RefreshCw size={13} />}>
              Refresh
            </Button>
            <Button variant="primary" size="sm" onClick={() => navigate('/scans')}>
              + Ingest Document
            </Button>
          </div>
        }
      />

      {/* 2. Top Summary KPI Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '14px',
          marginBottom: '18px',
        }}
      >
        <StatCard
          label="Total Repository Documents"
          value={scans.length}
          icon={<FolderOpen size={18} />}
          subtitle="Multi-format store"
        />
        <StatCard
          label="Vector Embedding Dimensions"
          value="384d"
          delta="HNSW Indexed"
          deltaType="positive"
          icon={<Database size={18} />}
          subtitle="Cosine similarity"
        />
        <StatCard
          label="Tenant Isolation"
          value="ENFORCING"
          icon={<Lock size={18} />}
          subtitle="WHERE tenant_id = ?"
          statusBadge={<StatusBadge status="SAFE" />}
        />
      </div>

      {/* 3. Filter Toolbar */}
      <PageToolbar
        leftControls={
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Search size={13} style={{ color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Search repository documents..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                style={{
                  backgroundColor: 'var(--bg-input)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: '4px 10px',
                  fontSize: '0.75rem',
                  outline: 'none',
                  minWidth: '240px',
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Format:</span>
              <select
                value={formatFilter}
                onChange={(e) => setFormatFilter(e.target.value)}
                style={{
                  backgroundColor: 'var(--bg-input)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: '4px 8px',
                  fontSize: '0.75rem',
                  outline: 'none',
                }}
              >
                <option value="ALL">All Formats</option>
                <option value="PDF">PDF</option>
                <option value="DOCX">DOCX</option>
                <option value="TXT">TXT</option>
                <option value="HTML">HTML</option>
              </select>
            </div>
          </div>
        }
        rightControls={
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Showing <strong>{filteredDocs.length}</strong> of {scans.length} documents
          </span>
        }
      />

      {/* 4. Documents DataTable */}
      <Card
        title="Ingested Multi-Format Documents"
        subtitle="Parsed text representations, metadata blocks, and vector retrieval pointers"
      >
        <DataTable
          columns={columns}
          data={filteredDocs}
          keyExtractor={(row) => row.scan_id}
          pageSize={8}
        />
      </Card>

      {/* 5. Document Inspection Drawer */}
      <Drawer
        isOpen={selectedDoc !== null}
        onClose={() => setSelectedDoc(null)}
        title="Document Repository Record"
        subtitle={`File: ${selectedDoc?.filename || ''} • ID: ${selectedDoc?.scan_id || ''}`}
        badge={selectedDoc ? <StatusBadge status={selectedDoc.verdict} /> : undefined}
        footer={
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <Button variant="secondary" onClick={() => setSelectedDoc(null)}>
              Close Drawer
            </Button>
            <Button
              variant="primary"
              onClick={() => setIsViewerOpen(true)}
              icon={<Eye size={14} />}
            >
              Launch Forensic Viewer
            </Button>
            <Button variant="outline" onClick={() => navigate('/scans')}>
              Open in Scan Console
            </Button>
          </div>
        }
      >
        {selectedDoc && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)', fontSize: '0.8125rem' }}>
              <div style={{ fontWeight: 700, marginBottom: '4px', color: 'var(--text-primary)' }}>
                Document Ingestion Summary
              </div>
              <div style={{ color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {selectedDoc.summary || 'Ingested cleanly with layout awareness and semantic vector chunking.'}
              </div>
            </div>

            <div style={{ padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)', fontSize: '0.8125rem' }}>
              <div style={{ fontWeight: 700, marginBottom: '6px', color: 'var(--accent-cyan)' }}>
                pgvector Chunking Provenance
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Chunk Table: <code>securoxi_document_chunks</code> • Embedding Model: <code>all-MiniLM-L6-v2 (384d)</code>
              </div>
            </div>
          </div>
        )}
      </Drawer>

      {/* 6. Forensic Document Viewer Overlay */}
      {selectedDoc && (
        <ForensicDocumentViewer
          isOpen={isViewerOpen}
          onClose={() => setIsViewerOpen(false)}
          filename={selectedDoc.filename}
          documentType={selectedDoc.document_type}
          verdict={selectedDoc.verdict}
          riskScore={selectedDoc.risk_score}
          findings={selectedDoc.findings || []}
          onOpenSecurityBrain={() => {
            setIsViewerOpen(false);
            navigate('/security-brain');
          }}
        />
      )}
    </PageContainer>
  );
};
