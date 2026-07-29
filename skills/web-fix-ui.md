# `/web-fix-ui` Skill — UI Overflow, Animation & Layout Repair

Use this skill when diagnosing or resolving layout bugs, CSS overlaps, broken animations, or mobile responsiveness issues.

---

## Workflow Steps

1. **Locate Target Files**:
   - Check `registry/<site_id>.md` to identify framework, CSS setup (Tailwind v3 vs v4, vanilla CSS, CSS modules), and page structure.

2. **Inspect & Isolate**:
   - Check for fixed widths (`width: 100vw` or hardcoded pixel widths) causing `overflow-x`. Replace with `w-full` or `max-w-full`.
   - Check z-index stacking context issues causing menu/modal overlaps.
   - Verify flexbox/grid wrapper properties (`flex-wrap`, `min-w-0`).

3. **Apply & Verify**:
   - Make targeted CSS/JSX edits preserving overall design tokens and micro-interactions.
   - Run `npm run build` in the target site repository to ensure zero build errors.
