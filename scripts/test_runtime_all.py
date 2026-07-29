"""
Web-Ops OS Full Runtime Execution Test Suite
Executes every script in scripts/ as an isolated subprocess, verifying exit code 0,
correct path resolution, zero uncaught exceptions, and clean execution.
"""

import os
import sys
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

SCRIPTS_TO_TEST = [
    "health_check.py",
    "backend_deep_probe.py",
    "sec_audit.py",
    "seo_scanner.py",
    "visual_audit.py",
    "auto_fixer.py",
    "agent_autonomous_runner.py",
    "cloud_runner.py",
    "sync_registry.py",
    "update_website_manager.py"
]

def run_script_test(script_name):
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        return False, f"Script not found: {script_path}"
        
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        res = subprocess.run(
            [sys.executable, script_path],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=30
        )
        if res.returncode == 0:
            return True, f"Exit code 0 | Output length: {len(res.stdout)} chars"
        else:
            stderr_snippet = res.stderr[-300:] if res.stderr else res.stdout[-300:]
            return False, f"Exit code {res.returncode} | Error: {stderr_snippet.strip()}"
    except Exception as e:
        return False, f"Execution exception: {e}"

def main():
    print("=" * 70)
    print(" 🧪 WEB-OPS OS — RUNTIME EXECUTION TEST SUITE")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for script_name in SCRIPTS_TO_TEST:
        print(f"\n[TESTING RUNTIME EXECUTION] {script_name}...")
        ok, msg = run_script_test(script_name)
        if ok:
            print(f" 🟢 [PASS] {script_name} — {msg}")
            passed += 1
        else:
            print(f" 🔴 [FAIL] {script_name} — {msg}")
            failed += 1
            
    print("\n" + "=" * 70)
    print(f" RUNTIME TEST RESULT: {passed} PASSED / {failed} FAILED")
    print("=" * 70)
    
    if failed > 0:
        sys.exit(1)
    else:
        print(" 🎉 ALL AUTOMATION SCRIPTS PASSED LIVE RUNTIME EXECUTION.")

if __name__ == "__main__":
    main()
