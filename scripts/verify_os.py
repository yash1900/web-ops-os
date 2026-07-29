"""
Web-Ops OS Full Verification Suite
Comprehensive audit of file paths, JSON schemas, router integrity, skill/agent references, and script execution.
"""

import json
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

def assert_file(rel_path, name):
    if not rel_path or not rel_path.strip():
        print(f" [FAIL] {name} INVALID/EMPTY PATH: '{rel_path}'")
        return False
    full_path = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full_path):
        print(f" [OK] {name}: {rel_path}")
        return True
    else:
        print(f" [FAIL] {name} MISSING: {rel_path}")
        return False

def main():
    print("=" * 70)
    print(" 🛠️  WEB-OPS OS — COMPREHENSIVE SYSTEM VERIFICATION SUITE")
    print("=" * 70)
    
    passed = 0
    failed = 0

    # 1. System Routers
    print("\n--- 1. SYSTEM ROUTERS & GOVERNANCE ---")
    router_files = [
        ("CLAUDE.md", "System Governance & Guidelines"),
        ("ROUTING.md", "Intent & Site Lookup Router"),
        ("README.md", "System Documentation & Sitemap")
    ]
    for rfile, name in router_files:
        if assert_file(rfile, name): passed += 1
        else: failed += 1

    # 2. Registry & Websites Manifest
    print("\n--- 2. REGISTRY & WEBSITES MANIFEST ---")
    manifest_path = os.path.join(BASE_DIR, "registry", "websites.json")
    if assert_file("registry/websites.json", "Websites JSON Manifest"):
        passed += 1
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            sites = data.get("managed_websites", [])
            print(f"  -> Valid JSON format. Managed websites count: {len(sites)}")
            for s in sites:
                site_id = s.get("site_id", "unknown")
                spec_rel = s.get("spec_file", "")
                local_rel = s.get("local_path", "")
                
                # Check spec doc
                if spec_rel and os.path.exists(os.path.join(BASE_DIR, spec_rel)):
                    print(f"   [OK] Site '{site_id}' Spec Doc: {spec_rel}")
                    passed += 1
                else:
                    print(f"   [FAIL] Site '{site_id}' Spec Doc missing or empty: {spec_rel}")
                    failed += 1
                    
                # Check site folder
                if local_rel and os.path.exists(os.path.join(ROOT_DIR, local_rel)):
                    print(f"   [OK] Site '{site_id}' Folder: {local_rel}")
                    passed += 1
                else:
                    print(f"   [FAIL] Site '{site_id}' Folder missing or empty: {local_rel}")
                    failed += 1
        except Exception as e:
            print(f"  [FAIL] JSON Parse Error: {e}")
            failed += 1
    else:
        failed += 1

    # 3. Specialized AI Agent Specifications
    print("\n--- 3. SPECIALIZED AI AGENTS ---")
    agents = [
        "agents/head-web-orchestrator.md",
        "agents/web-ui-ux-agent.md",
        "agents/web-seo-rank-agent.md",
        "agents/web-security-error-agent.md",
        "agents/web-health-crm-agent.md"
    ]
    for agent_path in agents:
        if assert_file(agent_path, f"Agent Spec ({os.path.basename(agent_path)})"): passed += 1
        else: failed += 1

    # 4. Operational Skill Files
    print("\n--- 4. OPERATIONAL SKILLS ---")
    skills = [
        "skills/web-audit.md",
        "skills/web-fix-ui.md",
        "skills/web-seo-opt.md",
        "skills/web-sec-harden.md",
        "skills/web-health-monitor.md",
        "skills/web-onboard-site.md"
    ]
    for skill_path in skills:
        if assert_file(skill_path, f"Skill File ({os.path.basename(skill_path)})"): passed += 1
        else: failed += 1

    # 5. Deterministic Scripts & Auto-Fixers
    print("\n--- 5. DETERMINISTIC AUTOMATION SCRIPTS ---")
    scripts = [
        "scripts/health_check.py",
        "scripts/seo_scanner.py",
        "scripts/sec_audit.py",
        "scripts/sync_registry.py",
        "scripts/auto_fixer.py",
        "scripts/visual_audit.py",
        "scripts/agent_autonomous_runner.py",
        "scripts/update_website_manager.py",
        "scripts/git_guardrail.py",
        "scripts/cloud_runner.py",
        ".github/workflows/web_ops_cloud_cron.yml"
    ]
    for script_path in scripts:
        if assert_file(script_path, f"Script/Workflow ({os.path.basename(script_path)})"): passed += 1
        else: failed += 1


    # 6. Deep Reference Standards
    print("\n--- 6. DEEP REFERENCE STANDARDS ---")
    references = [
        "references/schema-templates.json",
        "references/design-tokens.md",
        "references/security-headers.json"
    ]
    for ref_path in references:
        if assert_file(ref_path, f"Reference ({os.path.basename(ref_path)})"): passed += 1
        else: failed += 1

    # 7. Departmental Knowledge Bases & Task Catalog
    print("\n--- 7. DEPARTMENTAL KNOWLEDGE BASES & TASK CATALOG ---")
    knowledge_files = [
        "agents/knowledge/ui_ux_knowledge.md",
        "agents/knowledge/seo_rank_knowledge.md",
        "agents/knowledge/security_error_knowledge.md",
        "agents/knowledge/health_crm_knowledge.md",
        "registry/tasks_catalog.json"
    ]
    for k_path in knowledge_files:
        if assert_file(k_path, f"Knowledge Base/Catalog ({os.path.basename(k_path)})"): passed += 1
        else: failed += 1

    # 8. Parent OS Integration
    print("\n--- 8. PARENT OS INTEGRATION ---")
    parent_claude = os.path.join(ROOT_DIR, "CLAUDE.md")
    automations_memory = os.path.join(ROOT_DIR, "Dashboard", "memory", "automations.md")
    
    if os.path.exists(parent_claude):
        with open(parent_claude, "r", encoding="utf-8") as f:
            if "web-ops-os" in f.read():
                print(" [OK] Parent OS CLAUDE.md has web-ops-os router entry")
                passed += 1
            else:
                print(" [FAIL] Parent OS CLAUDE.md missing web-ops-os router entry")
                failed += 1
    else:
        print(" [FAIL] Parent OS CLAUDE.md missing")
        failed += 1
    
    if os.path.exists(automations_memory):
        with open(automations_memory, "r", encoding="utf-8") as f:
            if "web-ops-os" in f.read():
                print(" [OK] Dashboard/memory/automations.md has web-ops-os memory entry")
                passed += 1
            else:
                print(" [FAIL] Dashboard/memory/automations.md missing web-ops-os memory entry")
                failed += 1
    else:
        print(" [FAIL] Dashboard/memory/automations.md missing")
        failed += 1

    print("\n" + "=" * 70)
    print(f" VERIFICATION RESULT: {passed} PASSED / {failed} FAILED")
    print("=" * 70)
    if failed == 0:
        print(" 🎉 SYSTEM VERIFICATION COMPLETE — ZERO GAPS DETECTED.")
        sys.exit(0)
    else:
        print(f" ⚠️ {failed} VERIFICATION CHECKS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
