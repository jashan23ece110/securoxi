"""
SECUROXI AI Command Line Interface (CLI) & Demo Runner
"""

import sys
import os
import argparse
import json
from securoxi import __version__
from securoxi.config import SecuroxiConfig
from securoxi.scanner import SecuroxiScanner


def print_banner():
    banner = f"""
=====================================================
  SECUROXI AI - Document Prompt Injection Detector
  Version: {__version__} | Stage 1 (End-to-End Test Unit)
=====================================================
"""
    print(banner)


def format_report_text(report_dict: dict) -> str:
    lines = []
    lines.append("=" * 70)
    lines.append("                 SECUROXI SECURITY SCAN REPORT")
    lines.append("=" * 70)
    lines.append(f"File Name                  : {report_dict['filename']}")
    lines.append(f"Document Format            : {report_dict['document_type']}")
    
    verdict = report_dict['verdict']
    verdict_symbol = "🟢" if verdict == "SAFE" else ("🟡" if verdict == "SUSPICIOUS" else "🔴")
    lines.append(f"Verdict                    : {verdict_symbol} {verdict}")
    lines.append(f"Risk Score                 : {report_dict['risk_score']}/100")
    if report_dict.get('primary_threat'):
        lines.append(f"Primary Threat Signal      : {report_dict['primary_threat']}")
    lines.append(f"Overall Confidence         : {report_dict['overall_confidence'] * 100:.0f}%")
    lines.append(f"Total Spans Analyzed       : {report_dict['total_spans_analyzed']}")
    lines.append(f"Total Security Findings    : {report_dict['findings_count']}")
    lines.append(f"Execution Timing           : {report_dict['execution_time_ms']} ms")
    lines.append("-" * 70)
    lines.append(f"Verdict Summary: {report_dict['verdict_explanation']}")

    if report_dict.get('attack_chains'):
        lines.append("-" * 70)
        lines.append("⛓️ CORRELATED ATTACK CHAINS SYNTHESIZED:")
        for chain in report_dict['attack_chains']:
            lines.append(f"   • [{chain['chain_id']}] {chain['title']} ({chain['severity']})")
            lines.append(f"     Description: {chain['description']}")
            lines.append(f"     Contributing Categories: {', '.join(chain['contributing_categories'])}")

    if report_dict.get('top_contributing_evidence'):
        lines.append("-" * 70)
        lines.append("🎯 TOP RISK-CONTRIBUTING EVIDENCE:")
        for idx, top in enumerate(report_dict['top_contributing_evidence'], 1):
            lines.append(f"   {idx}. {top['title']} [{top['category']}] (Impact: +{top['impact_score']})")
            lines.append(f"      Location: {top['location']}")
            lines.append(f"      Original Text: \"{top['original_text']}\"")

    if report_dict.get('correlated_evidence'):
        lines.append("-" * 70)
        lines.append("⚡ CORRELATED THREAT COMBINATIONS DETECTED:")
        for ev in report_dict['correlated_evidence']:
            lines.append(f"   • {ev}")

    lines.append("-" * 70)

    findings = report_dict.get('findings', [])
    if not findings:
        lines.append("No security issues detected. Document appears SAFE.")
    else:
        # Separate Visual Deception vs Prompt Injection Findings for clear reporting
        visual_findings = [f for f in findings if f['category'] in (
            "MICRO_TEXT", "WHITE_TEXT", "BACKGROUND_MATCH", "HIDDEN_TEXT", "INVISIBLE_UNICODE", "SUSPICIOUS_POSITION", "VISUAL_DECEPTION"
        )]
        injection_findings = [f for f in findings if f not in visual_findings]

        if visual_findings:
            lines.append("👁️ VISUAL DECEPTION FINDINGS:")
            for idx, f in enumerate(visual_findings, 1):
                lines.append(f"   [{idx}] {f['title']} ({f['severity']})")
                lines.append(f"       Category   : {f['category']}")
                lines.append(f"       Location   : {f['location'] or 'N/A'}")
                lines.append(f"       Confidence : {f['confidence'] * 100:.0f}%")
                lines.append(f"       Explanation: {f['description']}")
                lines.append(f"       Evidence   : \"{f['evidence']}\"")
                lines.append("")

        if injection_findings:
            lines.append("💉 PROMPT INJECTION & MANIPULATION FINDINGS:")
            for idx, f in enumerate(injection_findings, 1):
                lines.append(f"   [{idx}] {f['title']} ({f['severity']})")
                lines.append(f"       Category   : {f['category']}")
                lines.append(f"       Location   : {f['location'] or 'N/A'}")
                lines.append(f"       Confidence : {f['confidence'] * 100:.0f}%")
                lines.append(f"       Explanation: {f['description']}")
                lines.append(f"       Evidence   : \"{f['evidence']}\"")
                lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        prog="securoxi",
        description="SECUROXI AI: Document Security & Prompt Injection Detector"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: scan / analyze
    scan_parser = subparsers.add_parser("scan", aliases=["analyze"], help="Scan a document for visual deception and prompt injection")
    scan_parser.add_argument("file_path", help="Path to document file (.pdf)")
    scan_parser.add_argument("--json", action="store_true", help="Output report in JSON format")
    scan_parser.add_argument("--max-size-mb", type=int, default=10, help="Maximum file size limit in MB")

    args = parser.parse_args()

    if not args.command:
        print_banner()
        parser.print_help()
        sys.exit(0)

    if args.command in ("scan", "analyze"):
        file_path = args.file_path

        config = SecuroxiConfig(max_file_size_bytes=args.max_size_mb * 1024 * 1024)
        scanner = SecuroxiScanner(config=config)
        
        try:
            report_dict = scanner.scan_to_dict(file_path)

            if args.json:
                print(json.dumps(report_dict, indent=2))
            else:
                print_banner()
                print(format_report_text(report_dict))
        except Exception as e:
            print(f"Scan Failure: {str(e)}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
