# Isaan Tea Website Knowledge Base (`isaan-tea`)

> Canonical URL: [isaantea.com](https://isaantea.com)  
> Local Path: `Isaan_Tea_V1/`  
> GitHub Repository: `yash1900/isaan-tea`  
> Hosting: Vercel (`isaantea` project)  
> Router & Guidelines: [Isaan_Tea_V1/CLAUDE.md](file:///c:/Users/amar1/Downloads/Automations/Isaan_Tea_V1/CLAUDE.md)

---

## 1. Stack & Technical Architecture
- **Framework**: React 19 + Vite 6 + TypeScript.
- **Styling**: Tailwind CSS v4.
- **Backend / API**: Vercel Serverless Functions (`api/` directory) + Node Server (`server.ts`).
- **Integrations**: Google Sheets API (via `isaan-sa-key.json` service account / `GOOGLE_SA_JSON`), WhatsApp Business API, CRM Sales Funnel webhook triggers.

---

## 2. Business Scope & Content Focus
- B2B International Bulk Tea Exports (CTC, Orthodox, Specialty Assam/Darjeeling teas).
- Client lead inquiry forms, wholesale samples request, compliance certificates display (FSSAI, Spices Board, ISO).

---

## 3. SEO & Page Rank Metadata
- **Target Keywords**: Bulk Assam tea supplier, Orthodox tea exporter India, CTC tea bulk purchase, private label tea manufacturer.
- **Metadata**: Structured Schema.org Organization + Product markup in `index.html`.

---

## 4. Key Commands
- Dev Server: `npm run dev`
- Production Build: `npm run build`
- Deploy: `vercel --prod`
