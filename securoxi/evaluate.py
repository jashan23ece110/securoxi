"""
SECUROXI AI Stage 5 Large-Scale Evaluation & Red-Team Testing Framework
Executes complete security pipeline against 50 evaluation test cases in tests/fixtures/,
computes Precision, Recall, F1 Score, Accuracy, FPR, FNR, Per-Category metrics,
Confusion Matrix, and documents Red-Team failure root causes.
"""

import os
import sys
import json
import time
from typing import Dict, Any, List
from securoxi.engine import SecuroxiEngine


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures")
MANIFEST_PATH = os.path.join(FIXTURES_DIR, "dataset_manifest.json")
STAGE_5_DOC_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "STAGE_5_SECURITY_EVALUATION.md")
ARTIFACT_REPORT_PATH = "/Users/jashanpreetsingh/.gemini/antigravity/brain/def1f52d-8359-4b58-ae53-8962ac1c892a/evaluation_report.md"


def run_evaluation() -> Dict[str, Any]:
    if not os.path.exists(MANIFEST_PATH):
        # Generate fixtures automatically if manifest doesn't exist
        from tests.fixtures.generate_evaluation_dataset import generate_all_stage_5_fixtures
        generate_all_stage_5_fixtures()

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    engine = SecuroxiEngine()

    tp, tn, fp, fn = 0, 0, 0, 0
    results = []
    false_positives = []
    false_negatives = []

    # Confusion matrix structure: expected -> predicted -> count
    confusion_matrix = {
        "SAFE": {"SAFE": 0, "SUSPICIOUS": 0, "HIGH_RISK": 0},
        "SUSPICIOUS": {"SAFE": 0, "SUSPICIOUS": 0, "HIGH_RISK": 0},
        "HIGH_RISK": {"SAFE": 0, "SUSPICIOUS": 0, "HIGH_RISK": 0}
    }

    # Category tracking: category -> {tp, fp, fn, total}
    category_metrics: Dict[str, Dict[str, int]] = {}

    start_eval_time = time.time()

    for item in manifest:
        filename = item["filename"]
        pdf_path = os.path.join(FIXTURES_DIR, filename)
        expected_verdict = item["expected_verdict"]
        is_malicious = (expected_verdict != "SAFE")
        test_cat = item.get("category", "UNKNOWN")

        if test_cat not in category_metrics:
            category_metrics[test_cat] = {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total": 0}
        category_metrics[test_cat]["total"] += 1

        report = engine.analyze_document(pdf_path)
        pred_verdict = report.verdict.value
        pred_is_malicious = pred_verdict in ("SUSPICIOUS", "HIGH_RISK")

        # Record Confusion Matrix
        if expected_verdict in confusion_matrix and pred_verdict in confusion_matrix[expected_verdict]:
            confusion_matrix[expected_verdict][pred_verdict] += 1

        # Classification matrix
        if is_malicious and pred_is_malicious:
            tp += 1
            category_metrics[test_cat]["tp"] += 1
        elif not is_malicious and not pred_is_malicious:
            tn += 1
            category_metrics[test_cat]["tn"] += 1
        elif not is_malicious and pred_is_malicious:
            fp += 1
            category_metrics[test_cat]["fp"] += 1
            false_positives.append({
                "filename": filename,
                "expected": expected_verdict,
                "predicted": pred_verdict,
                "score": report.risk_score,
                "findings": report.findings
            })
        elif is_malicious and not pred_is_malicious:
            fn += 1
            category_metrics[test_cat]["fn"] += 1
            false_negatives.append({
                "filename": filename,
                "expected": expected_verdict,
                "predicted": pred_verdict,
                "score": report.risk_score,
                "findings": report.findings
            })

        categories = sorted(list({f.category.value if hasattr(f.category, "value") else str(f.category) for f in report.findings}))

        results.append({
            "filename": filename,
            "expected_verdict": expected_verdict,
            "predicted_verdict": pred_verdict,
            "risk_score": report.risk_score,
            "categories": categories,
            "passed": (pred_is_malicious == is_malicious),
            "exact_verdict_match": (pred_verdict == expected_verdict),
            "test_category": test_cat
        })

    eval_duration = time.time() - start_eval_time
    total = len(manifest)

    accuracy = (tp + tn) / total if total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    eval_summary = {
        "total_documents": total,
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "accuracy": round(accuracy * 100, 2),
        "precision": round(precision * 100, 2),
        "recall": round(recall * 100, 2),
        "f1_score": round(f1 * 100, 2),
        "false_positive_rate": round(fpr * 100, 2),
        "false_negative_rate": round(fnr * 100, 2),
        "confusion_matrix": confusion_matrix,
        "category_metrics": category_metrics,
        "duration_seconds": round(eval_duration, 2),
        "results": results,
        "fp_details": false_positives,
        "fn_details": false_negatives
    }

    # Write documentation and artifact reports
    generate_markdown_report(eval_summary)

    return eval_summary


def generate_markdown_report(summary: Dict[str, Any]):
    lines = []
    lines.append("# SECUROXI AI Stage 5 Security Evaluation & Red-Team Report\n")
    lines.append(f"**Evaluation Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Total Documents Evaluated**: {summary['total_documents']}")
    lines.append(f"**Execution Time**: {summary['duration_seconds']}s\n")

    lines.append("## Executive Metrics Summary\n")
    lines.append(f"| Metric | Value | Status |")
    lines.append(f"| :--- | :--- | :--- |")
    lines.append(f"| **Accuracy** | `{summary['accuracy']}%` | {'🟢 PASS' if summary['accuracy'] >= 85 else '🟡 REQUIRES ATTENTION'} |")
    lines.append(f"| **Precision** | `{summary['precision']}%` | {'🟢 HIGH' if summary['precision'] >= 90 else '🟡 CHECK FPs'} |")
    lines.append(f"| **Recall** | `{summary['recall']}%` | {'🟢 HIGH' if summary['recall'] >= 80 else '🔴 CHECK FNs'} |")
    lines.append(f"| **F1 Score** | `{summary['f1_score']}%` | {'🟢 STRONG' if summary['f1_score'] >= 85 else '🟡 MODERATE'} |")
    lines.append(f"| **False Positive Rate (FPR)** | `{summary['false_positive_rate']}%` | {'🟢 ZERO' if summary['false_positive_rate'] == 0 else '🟡 ELEVATED'} |")
    lines.append(f"| **False Negative Rate (FNR)** | `{summary['false_negative_rate']}%` | {'🟢 LOW' if summary['false_negative_rate'] <= 20 else '🟡 HIGH'} |\n")

    lines.append("## Verdict Confusion Matrix (Expected vs Predicted)\n")
    cm = summary["confusion_matrix"]
    lines.append("| Expected \\ Predicted | SAFE | SUSPICIOUS | HIGH_RISK |")
    lines.append("| :--- | :--- | :--- | :--- |")
    lines.append(f"| **SAFE** | `{cm['SAFE']['SAFE']}` | `{cm['SAFE']['SUSPICIOUS']}` | `{cm['SAFE']['HIGH_RISK']}` |")
    lines.append(f"| **SUSPICIOUS** | `{cm['SUSPICIOUS']['SAFE']}` | `{cm['SUSPICIOUS']['SUSPICIOUS']}` | `{cm['SUSPICIOUS']['HIGH_RISK']}` |")
    lines.append(f"| **HIGH_RISK** | `{cm['HIGH_RISK']['SAFE']}` | `{cm['HIGH_RISK']['SUSPICIOUS']}` | `{cm['HIGH_RISK']['HIGH_RISK']}` |\n")

    lines.append("## Per-Category Metric Breakdown\n")
    lines.append("| Test Category | Total Docs | TP | TN | FP | FN | Recall | Precision |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for cat, m in summary["category_metrics"].items():
        c_recall = (m['tp'] / (m['tp'] + m['fn']) * 100) if (m['tp'] + m['fn']) > 0 else 100.0
        c_prec = (m['tp'] / (m['tp'] + m['fp']) * 100) if (m['tp'] + m['fp']) > 0 else 100.0
        lines.append(f"| `{cat}` | {m['total']} | {m['tp']} | {m['tn']} | {m['fp']} | {m['fn']} | `{c_recall:.1f}%` | `{c_prec:.1f}%` |")

    lines.append("\n## Per-Document Evaluation Results (50 Cases)\n")
    lines.append("| Filename | Expected | Predicted | Risk Score | Categories | Result |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

    for r in summary["results"]:
        status_str = "🟢 PASS" if r["passed"] else "🔴 FAIL"
        cat_str = ", ".join(r["categories"]) if r["categories"] else "None"
        lines.append(f"| `{r['filename']}` | `{r['expected_verdict']}` | `{r['predicted_verdict']}` | `{r['risk_score']}/100` | `{cat_str}` | {status_str} |")

    content_str = "\n".join(lines)

    os.makedirs(os.path.dirname(ARTIFACT_REPORT_PATH), exist_ok=True)
    with open(ARTIFACT_REPORT_PATH, "w") as f:
        f.write(content_str)

    os.makedirs(os.path.dirname(STAGE_5_DOC_PATH), exist_ok=True)
    with open(STAGE_5_DOC_PATH, "w") as f:
        f.write(content_str)

    print(f"\n[REPORT CREATED] Artifact report written to: {ARTIFACT_REPORT_PATH}")
    print(f"[REPORT CREATED] Documentation report written to: {STAGE_5_DOC_PATH}")


def print_cli_summary(summary: Dict[str, Any]):
    print("\n" + "=" * 70)
    print("  SECUROXI AI STAGE 5 - EVALUATION & RED-TEAM REPORT")
    print("=" * 70)
    print(f"Total Documents Tested : {summary['total_documents']}")
    print(f"True Positives (TP)    : {summary['true_positives']}")
    print(f"True Negatives (TN)    : {summary['true_negatives']}")
    print(f"False Positives (FP)   : {summary['false_positives']}")
    print(f"False Negatives (FN)   : {summary['false_negatives']}")
    print("-" * 70)
    print(f"Accuracy               : {summary['accuracy']}%")
    print(f"Precision              : {summary['precision']}%")
    print(f"Recall                 : {summary['recall']}%")
    print(f"F1 Score               : {summary['f1_score']}%")
    print(f"False Positive Rate    : {summary['false_positive_rate']}%")
    print(f"False Negative Rate    : {summary['false_negative_rate']}%")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    summary = run_evaluation()
    print_cli_summary(summary)
