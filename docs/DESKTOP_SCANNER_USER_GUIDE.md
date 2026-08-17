# SECUROXI AI — Desktop Scanner User Guide

**Target Audience**: Security Analysts, Recruiters, Compliance Administrators  
**App**: SECUROXI Desktop Folder Scanner & Enterprise Local Agent  

---

## 1. Quick Start

1. **Launch the Scanner**: Open **SECUROXI Scanner** or run `securoxi agent scan /path/to/folder`.
2. **Sign In**: Authorize the scanner through your organization's SECUROXI Single Sign-On (SSO) browser session.
3. **Select Folder**: Choose your local resumes or document directory (e.g. `Company_Resumes_2026`).
4. **Review Pre-Flight Discovery**:
   - Total Files Discovered (e.g. `18,472`)
   - Supported Documents (e.g. `18,021`)
   - Duplicates Identified (e.g. `581 skipped`)
5. **Start Scan**: Click **START SCAN**. SECUROXI begins batching and uploading documents securely over TLS.
6. **Monitor on Web**: Open the SECUROXI Web Console (`/scan-folder` or `/scans`) to inspect real-time progress and investigate security findings.

---

## 2. Supported File Formats

* **Documents**: `.pdf`, `.docx`, `.doc`, `.txt`, `.rtf`
* **Scanned Images**: `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`

---

## 3. Resilience & Offline Handling

* **Network Interruption**: The scanner automatically pauses and resumes with exponential backoff when connectivity returns.
* **Computer Sleep or Restart**: Local state is persisted in an embedded SQLite queue (`~/.securoxi/agent_queue.db`). Completed files will never be re-uploaded.
* **Duplicate Detection**: Files with matching SHA-256 hashes are automatically recognized and deduplicated locally.

---

## 4. Privacy & Data Safety

* **Read-Only**: SECUROXI never modifies, overwrites, or deletes files on your computer.
* **Sandboxed Access**: Only files within the explicitly selected directory are processed. Symlinks pointing outside the folder are rejected.
* **Zero Local Execution**: Document scripts and macros are never executed on your device.
