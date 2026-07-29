# Fraterny Platform Knowledge Base (`fraterny`)

> Canonical URL: [fraterny.com](https://fraterny.com)  
> Local Path: `fraterny-automation/Fraterny_Nextjs` & `Quest`  
> GitHub Repository: `yash1900/fraterny`  
> Hosting: Vercel (Frontend) + GCP Compute Engine (Quest API Backend) + Supabase (Database)  
> Router & Guidelines: [fraterny-automation/CLAUDE.md](file:///c:/Users/amar1/Downloads/Automations/fraterny-automation/CLAUDE.md)

---

## 1. Stack & Technical Architecture
- **Frontend**: Next.js 14 App Router, TypeScript, Tailwind CSS, Vercel host.
- **Backend**: Quest API Node.js backend on GCP, PayPal & Stripe payment webhooks.
- **Database**: Supabase PostgreSQL (`pmaylemigtnzirbtiueg`).
- **Automation Pipeline**: Zero-maintenance webhook verifiers & error fallback handlers (`BUG3_PAYMENT_WEBHOOK_PLAN.md`).

---

## 2. Key Maintenance Tasks
- Webhook resilience & payment failure fallback mechanisms.
- API endpoint health monitoring for Quest backend.
- UI component consistency between Frat Villa and Quest dashboards.

---

## 3. SEO & Page Rank Metadata
- **Target Keywords**: Real estate investment platform, fractional villa ownership, property tech platform.
- **Metadata**: Next.js Metadata API in `app/layout.tsx` with dynamic OpenGraph generation.
