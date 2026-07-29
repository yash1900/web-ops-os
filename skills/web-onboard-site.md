# `/web-onboard-site` Skill — Standardized Website Onboarding Workflow

Use this skill when onboarding a new website or domain into `web-ops-os`.

---

## Onboarding Steps

1. **Register Entry**:
   - Add new site object to `registry/websites.json` with `site_id`, `name`, `local_path`, `production_url`, `tech_stack`, `hosting`, and `github_repo`.

2. **Create Knowledge Base Doc**:
   - Create `registry/<site_id>.md` detailing tech stack, build commands, domain setup, environment variable mapping, and known constraints.

3. **Update Router Files**:
   - Add route entry to `ROUTING.md` and `CLAUDE.md`.

4. **Verify Script Inclusion**:
   - Run `python scripts/sync_registry.py` to confirm the new site is picked up by `health_check.py`, `seo_scanner.py`, and `sec_audit.py`.
