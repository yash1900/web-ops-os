# `/scroll-craft` Skill — Premium Scroll-Driven Interactive Landing Pages

Use this skill when building or upgrading immersive, scroll-driven interactive landing pages for any brand or project (`personal-website`, `isaan-tea`, `fraterny`, `iconic-homes`).

---

## Core Capabilities
- **Timeline-based Scrollytelling**: Video scrubs frame-by-frame under the wheel, pinned stages, multi-act customer journey.
- **8 Distinct Page Grammars**: Filmic one-shot, chaptered editorial, live surface, continuous world, typographic poster, gallery, split stage, rhythmic cutlist.
- **Fingerprint Gate**: Guarantees each landing page differs on at least 4 of 6 dimensions (grammar, nav, hero, act shape, close, signature move).
- **Automated Verification Pass**: Headless browser captures snapshots across scroll positions, checks contrast compositing, detects dead scroll, and verifies asset decoding.

---

## Architecture & Locations
- **Engine & Scripts**: `web-ops-os/tools/scroll-craft/plugins/nateherk-design/skills/scroll-craft/`
- **Scoped Skill Definition**: `web-ops-os/.claude/skills/scroll-craft/SKILL.md`
- **Workspace & Fingerprint Registry**: `web-ops-os/tools/scroll-craft/scrollcraft/` (builds land in `builds/<name>/`, registry is `FINGERPRINTS.md`)

---

## Usage Commands
1. **Preflight Doctor Check**:
   ```powershell
   node tools/scroll-craft/plugins/nateherk-design/skills/scroll-craft/scripts/doctor.mjs
   ```
2. **Launch Interactive Skill**:
   - In Claude Code / Antigravity from within `web-ops-os`: invoke `/scroll-craft`.
   - Or dispatch `web-ui-ux-agent` with a scroll-driven landing page prompt.
