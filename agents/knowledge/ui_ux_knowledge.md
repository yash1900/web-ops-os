# UI/UX & Design Department Deep Knowledge Base

## Managed Codebase Component Trees
1. **Personal Website (`personal-website/`)**:
   - `src/App.tsx`: React Router v6 SPA routes.
   - `src/components/Constellation.tsx`: Three.js WebGL canvas background.
   - `src/pages/Mind.tsx`: Custom `requestAnimationFrame` scroll reveal system. (CRITICAL: Do NOT replace with IntersectionObserver).
2. **Isaan Tea (`Isaan_Tea_V1/`)**:
   - Tailwind CSS v4 setup, React 19 + Vite 6 layout components.
3. **Fraterny (`fraterny-automation/Fraterny_Nextjs`)**:
   - Next.js 14 App Router layout (`app/layout.tsx`).
4. **Iconic Homes (`Iconic-homes-Tulsi-tower/`)**:
   - Static HTML5 (`index.html`, `tulsi-tower.html`) + CSS3 layout.

## Layout & Responsive Boundaries
- Outer wrappers: `w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`
- Flex child safeguard: `min-w-0` to prevent text-node overflows.
- Overflow safeguard: `overflow-x-hidden` or `max-w-full`.
