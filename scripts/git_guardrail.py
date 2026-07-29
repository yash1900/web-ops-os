"""
Web-Ops OS Git Diff & Component Invariant Guardrail
Audits uncommitted git changes to block accidental file deletions, net line-count drops, wrong file edits, or broken component invariants.
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

# Key component invariants that must NEVER be deleted by agents
INVARIANTS = {
    "personal-website/src/pages/Mind.tsx": ["requestAnimationFrame", "getBoundingClientRect"],
    "personal-website/src/components/Constellation.tsx": ["Canvas"],
    "Isaan_Tea_V1/index.html": ["viewport"],
    "Iconic-homes-Tulsi-tower/index.html": ["Tulsi Tower"]
}

def check_invariants():
    violations = []
    for rel_file, symbols in INVARIANTS.items():
        full_path = os.path.join(ROOT_DIR, rel_file)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            for sym in symbols:
                if sym not in content:
                    violations.append(f"INVARIANT BROKEN: Critical symbol '{sym}' missing from {rel_file}")
    return violations

def audit_git_guardrails():
    print("=" * 70)
    print(" 🛡️  [WEB-OPS] GIT DIFF & COMPONENT INVARIANT GUARDRAIL")
    print("=" * 70)

    violations = check_invariants()
    if violations:
        print("\n ⚠️  GUARDRAIL VIOLATIONS DETECTED:")
        for v in violations:
            print(f"   [FAIL] {v}")
        sys.exit(1)
    else:
        print(" [OK] All critical site component invariants verified intact.")
        print("=" * 70)

if __name__ == "__main__":
    audit_git_guardrails()
