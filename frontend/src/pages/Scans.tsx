import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { ScanReport } from '../api/types';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { VerdictBadge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { LoadingState, EmptyState, ErrorState } from '../components/ui/States';

export const ScansPage: React.FC = () => {
  const [scans, setScans] = useState<ScanReport[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedScan, setSelectedScan] = useState<ScanReport | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchScans = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listScans();
      setScans(data);
      if (data.length > 0) {
        setSelectedScan(data[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch document scans.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScans();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setUploadError(null);
    }
  };

  const handleUploadAndScan = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadError(null);

    try {
      const report = await api.uploadAndScanDocument(selectedFile);
      setScans((prev) => [report, ...prev]);
      setSelectedScan(report);
      setSelectedFile(null);
    } catch (err: any) {
      setUploadError(err.message || 'Document security scan failed.');
    } finally {
      setIsUploading(false);
    }
  };

  if (loading) {
    return <LoadingState message="Connecting to Layout-Aware PDF Scanner & fetching scan history..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchScans} />;
  }

  const filteredScans = scans.filter(
    (s) =>
      s.filename.toLowerCase().includes(searchFilter.toLowerCase()) ||
      s.scan_id.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title Header */}
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span>🔍</span>
          <span>Document Security & On-Demand Scan Console</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Upload PDF documents or bulk ZIP archives for layout-aware prompt injection and visual deception analysis.
        </p>
      </div>

      {/* Upload Drag & Drop Console */}
      <Card title="Upload Payload for Threat Analysis" subtitle="Supports single PDF documents and compressed bulk ZIP archives (Max 10MB per PDF)">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div
            style={{
              border: '2px dashed var(--border-default)',
              borderRadius: 'var(--radius-lg)',
              padding: '32px',
              textAlign: 'center',
              backgroundColor: 'var(--bg-app)',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '32px', marginBottom: '8px' }}>📁</div>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
              Drag & Drop PDF or ZIP archive here, or browse files
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Supported: .pdf, .zip (Max 50 files / 50MB uncompressed)
            </div>

            <input
              type="file"
              accept=".pdf,.zip"
              onChange={handleFileChange}
              style={{ display: 'none' }}
              id="file-upload-input"
            />
            <label htmlFor="file-upload-input" className="btn btn-secondary" style={{ cursor: 'pointer' }}>
              Select File
            </label>
          </div>

          {selectedFile && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)' }}>
              <div>
                <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>Selected: {selectedFile.name}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '12px' }}>
                  ({(selectedFile.size / 1024).toFixed(1)} KB)
                </span>
              </div>
              <Button variant="primary" isLoading={isUploading} onClick={handleUploadAndScan}>
                Start Security Scan
              </Button>
            </div>
          )}

          {uploadError && <Alert type="danger" title="Scan Failed">{uploadError}</Alert>}
        </div>
      </Card>

      {/* Main Split View: History Table & Detailed Scan Inspection */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        {/* Scan History Table */}
        <Card title="Scan History" subtitle={`${scans.length} scans evaluated`}>
          <div style={{ marginBottom: '12px' }}>
            <input
              type="text"
              placeholder="Filter scans by filename..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '6px 12px',
                fontSize: '0.8125rem',
                color: 'var(--text-primary)',
              }}
            />
          </div>

          {filteredScans.length === 0 ? (
            <EmptyState title="No Scans Found" description="Upload a document above to generate threat analysis." />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '480px', overflowY: 'auto' }}>
              {filteredScans.map((s) => (
                <div
                  key={s.scan_id}
                  onClick={() => setSelectedScan(s)}
                  style={{
                    padding: '12px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: selectedScan?.scan_id === s.scan_id ? 'var(--bg-surface-elevated)' : 'var(--bg-app)',
                    border: selectedScan?.scan_id === s.scan_id ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>{s.filename}</span>
                    <VerdictBadge verdict={s.verdict} />
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ID: {s.scan_id} • Risk Score: {s.risk_score}/100</div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Selected Scan Report Inspection */}
        <div>
          {selectedScan ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <Card title={`Scan Report: ${selectedScan.filename}`} subtitle={`Scan ID: ${selectedScan.scan_id}`}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px', marginBottom: '16px' }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>VERDICT</div>
                    <VerdictBadge verdict={selectedScan.verdict} />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>RISK SCORE</div>
                    <div style={{ fontWeight: 800, fontSize: '1.25rem', color: selectedScan.risk_score > 70 ? 'var(--status-highrisk)' : 'var(--status-safe)' }}>
                      {selectedScan.risk_score} / 100
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>DOCUMENT TYPE</div>
                    <div style={{ fontWeight: 700 }}>{selectedScan.document_type}</div>
                  </div>
                </div>

                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', padding: '12px', background: 'var(--bg-app)', borderRadius: '6px' }}>
                  <strong>Summary:</strong> {selectedScan.summary || 'Document analysis completed cleanly.'}
                </div>
              </Card>

              {/* Findings & Evidence Table */}
              <Card title="Detected Findings & Forensic Evidence" subtitle={`${selectedScan.findings.length} threat patterns identified`}>
                {selectedScan.findings.length === 0 ? (
                  <Alert type="success" title="Clean Document">
                    No threat patterns, prompt injection instructions, or visual deception text spans were detected.
                  </Alert>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {selectedScan.findings.map((f, idx) => (
                      <div key={idx} style={{ padding: '12px', background: 'var(--bg-app)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                          <span style={{ fontWeight: 700, color: 'var(--status-highrisk)' }}>{f.threat_type}</span>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>Confidence: {(f.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>{f.description}</div>
                        <pre className="security-evidence">{f.evidence}</pre>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>
          ) : (
            <Card>
              <EmptyState title="Select a Scan" description="Click any scan from the history table to view detailed forensic reports." />
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
