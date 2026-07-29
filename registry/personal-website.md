# Personal Website Knowledge Base (`personal-website`)

> Canonical URL: [yashmalhotra.space](https://yashmalhotra.space)  
> Local Path: `personal-website/`  
> GitHub Repository: `yash1900/quiet-founder-notes`  
> Hosting: Vercel (`fraterny-website` scope, project `quiet-founder-notes`)  
> Router & Guidelines: [personal-website/CLAUDE.md](file:///c:/Users/amar1/Downloads/Automations/personal-website/CLAUDE.md)

---

## 1. Stack & Technical Architecture
- **Framework**: Vite + React 18 (`^18.3.1`), TypeScript (`^5.8.3`).
- **Styling**: Tailwind CSS 3 (`^3.4.17`), shadcn/ui (Radix UI components), `tailwindcss-animate`.
- **Hero & Graphics**: Three.js (`^0.185.1`) WebGL constellation canvas (`src/components/Constellation.tsx`).
- **Routing**: Client-side React Router v6 (`src/App.tsx`) with SPA rewrite in `vercel.json`.
- **Scroll Reveal System**: `requestAnimationFrame` + `getBoundingClientRect` in `src/pages/Mind.tsx`. (CRITICAL CONSTRAINT: Do NOT refactor to IntersectionObserver — IO delivery stalls on heavy WebGL page).

---

## 2. Positioning & Content Guardrails
- **Thesis-led**: "Cross-domain synthesis of psychology + capital + business + marketing + AI."
- **Isaan framing**: "Third-generation entrepreneur taking a family tea business international for the first time."
- **Excluded**: NOT employed by Iconic Homes (family business only). NO em dashes in site copy. NO "building in public" framing.

---

## 3. SEO & Page Rank Metadata
- **Title Tag**: `Yash Malhotra — Mind / OS`
- **Meta Description**: Interactive single-page scroll narrative on cross-domain synthesis, AI operations, and international tea exports.
- **OpenGraph / Twitter**: `og-source.svg`, custom Twitter card metadata in `index.html`.
- **Sitemap / Robots**: Clean robots.txt, single-page SPA routing.

---

## 4. Key Build & Dev Commands
- Dev Server: `npm run dev` (Port 8080)
- Production Build: `npm run build`
- Deploy: `git push origin main` auto-deploys to Vercel production.
- Manual Deploy: `vercel --prod --scope fraterny-website --yes`
