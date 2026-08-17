"""
SECUROXI AI Phase 2 Stage 9 — Benchmark Evaluator Engine
Evaluates Precision, Recall, F1, Security Gate Accuracy, and Irrelevance/Bias Robustness.
"""

import os
import sys
from typing import List, Dict, Any
from securoxi.config import SecuroxiConfig
from securoxi.screening.eval_dataset import generate_phase2_evaluation_dataset, EVAL_FIXTURES_DIR
from securoxi.screening.pipeline import SecuroxiScreeningPipeline


def run_phase2_screening_evaluation() -> Dict[str, Any]:
    """
    Executes Phase 2 Resume Screening Evaluation Benchmark.
    """
    config = SecuroxiConfig()
    pipeline = SecuroxiScreeningPipeline(config=config)
    dataset = generate_phase2_evaluation_dataset()

    jd_path = os.path.join(EVAL_FIXTURES_DIR, "..", "phase2", "sample_jd.txt")
    if not os.path.exists(jd_path):
        # Fallback inline JD
        jd_source = "SENIOR PYTHON SECURITY ENGINEER\nREQUIREMENTS\n- 5+ years experience in Python, PyMuPDF, and FastAPI."
    else:
        jd_source = jd_path

    tp, tn, fp, fn = 0, 0, 0, 0
    security_gate_correct = 0
    security_gate_total = 0
    bias_score_clean = 0.0
    bias_score_with_hobbies = 0.0

    eval_table: List[Dict[str, Any]] = []

    for item in dataset:
        filepath = item["filepath"]
        res = pipeline.screen_resume(filepath, jd_source)

        sec_verdict = res["security_verdict"]
        report = res["screening_report"]
        fit_score = report.get("match_score", 0.0)
        rec = report.get("recommendation", "INSUFFICIENT_DATA")

        # Security gate check
        if item["has_security_threat"]:
            security_gate_total += 1
            if sec_verdict == "HIGH_RISK":
                security_gate_correct += 1

        # Track bias test scores
        if item["filename"] == "candidate_strong_2.pdf":
            bias_score_clean = fit_score
        elif item.get("is_bias_test"):
            bias_score_with_hobbies = fit_score

        # Ground truth evaluation
        is_pos_pred = rec in ["STRONG_MATCH", "GOOD_MATCH"]
        is_pos_actual = item["is_relevant"]

        if is_pos_pred and is_pos_actual:
            tp += 1
        elif not is_pos_pred and not is_pos_actual:
            tn += 1
        elif is_pos_pred and not is_pos_actual:
            fp += 1
        elif not is_pos_pred and is_pos_actual:
            fn += 1

        eval_table.append({
            "filename": item["filename"],
            "expected_verdict": item["expected_verdict"],
            "actual_verdict": sec_verdict,
            "expected_rec": item["expected_recommendation"],
            "actual_rec": rec,
            "fit_score": fit_score
        })

    # Calculate metrics
    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0
    recall = (tp / (tp + fn)) if (tp + fn) > 0 else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    sec_gate_acc = (security_gate_correct / security_gate_total * 100.0) if security_gate_total > 0 else 100.0
    bias_score_delta = abs(bias_score_clean - bias_score_with_hobbies)

    return {
        "total_documents": len(dataset),
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision * 100.0, 2),
        "recall": round(recall * 100.0, 2),
        "f1": round(f1 * 100.0, 2),
        "security_gate_accuracy": round(sec_gate_acc, 2),
        "bias_score_delta": round(bias_score_delta, 2),
        "eval_table": eval_table
    }


if __name__ == "__main__":
    results = run_phase2_screening_evaluation()
    print("=" * 60)
    print("SECUROXI AI Phase 2 Resume Screening Evaluation Report")
    print("=" * 60)
    print(f"Total Evaluated: {results['total_documents']}")
    print(f"Precision: {results['precision']}%")
    print(f"Recall: {results['recall']}%")
    print(f"F1 Score: {results['f1']}%")
    print(f"Security Gate Accuracy: {results['security_gate_accuracy']}%")
    print(f"Bias Robustness (Score Delta): {results['bias_score_delta']} (0.0 = perfect)")
    print("=" * 60)
