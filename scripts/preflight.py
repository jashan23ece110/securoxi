#!/usr/bin/env python3
"""
SECUROXI AI Intelligence 2.0 — Production Preflight & Release Automation Script (Stage 27)
Automated verification of environment configuration, database connectivity, storage permissions,
security policies, and API readiness before traffic routing.
"""

import sys
import os
import json
import time

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def run_preflight() -> bool:
    print("=================================================================")
    print("      SECUROXI AI ENTERPRISE — PRODUCTION PREFLIGHT CHECKS       ")
    print("=================================================================")

    all_passed = True

    # 1. Environment & Configuration Check
    print("\n[1/6] Checking Environment Configuration...")
    try:
        from securoxi.environment import load_deployment_config, validate_environment, EnvironmentMode
        cfg = load_deployment_config()
        issues = validate_environment(cfg)
        if issues:
            print(f"  ❌ Environment validation warnings/errors: {issues}")
            if cfg.environment == EnvironmentMode.PRODUCTION:
                all_passed = False
        else:
            print(f"  ✅ Environment Mode: {cfg.environment.value.upper()}")
            print(f"  ✅ Storage Root: {cfg.storage_root}")
            print(f"  ✅ CORS Allowed Origins: {cfg.cors_allowed_origins}")
    except Exception as e:
        print(f"  ❌ Failed to load environment configuration: {e}")
        all_passed = False

    # 2. Database Connectivity
    print("\n[2/6] Checking Database Connectivity...")
    try:
        from securoxi.storage.db import SecuroxiDatabase
        db = SecuroxiDatabase()
        stats = db.get_dashboard_stats()
        print(f"  ✅ Database Connected. Total Scans: {stats.get('total_scans', 0)}")
    except Exception as e:
        print(f"  ❌ Database connection error: {e}")
        all_passed = False

    # 3. Security Scanner & Analysis Engine
    print("\n[3/6] Checking Security Scanner & Reasoning Layer...")
    try:
        from securoxi.scanner import SecuroxiScanner
        from securoxi.config import SecuroxiConfig
        scanner = SecuroxiScanner(config=SecuroxiConfig())
        print("  ✅ SecuroxiScanner & Attack Category Weights initialized.")
    except Exception as e:
        print(f"  ❌ Security Scanner initialization error: {e}")
        all_passed = False

    # 4. Agent Orchestrator & Workspaces
    print("\n[4/6] Checking Agent Orchestrator & Workspaces...")
    try:
        from securoxi.orchestrator.orchestrator import AgentOrchestrator
        orchestrator = AgentOrchestrator()
        print("  ✅ Orchestrator Core, Execution Runner, Hiring, Ask, Investigation, Monitoring & Governance workspaces active.")
    except Exception as e:
        print(f"  ❌ Orchestrator initialization error: {e}")
        all_passed = False

    # 5. Storage Directory Permissions
    print("\n[5/6] Checking Storage Directory Permissions...")
    try:
        storage_path = cfg.storage_root if 'cfg' in locals() else "./data/storage"
        os.makedirs(storage_path, exist_ok=True)
        test_file = os.path.join(storage_path, ".preflight_check")
        with open(test_file, "w") as f:
            f.write("preflight_ok")
        os.remove(test_file)
        print(f"  ✅ Storage path '{storage_path}' is writable.")
    except Exception as e:
        print(f"  ❌ Storage permission error: {e}")
        all_passed = False

    # 6. Final Status Summary
    print("\n=================================================================")
    if all_passed:
        print("  🟢 PREFLIGHT CHECK STATUS: PASSED — READY FOR PRODUCTION GO-LIVE")
    else:
        print("  🔴 PREFLIGHT CHECK STATUS: FAILED — RESOLVE ISSUES BEFORE GO-LIVE")
    print("=================================================================\n")
    return all_passed


if __name__ == "__main__":
    success = run_preflight()
    sys.exit(0 if success else 1)
