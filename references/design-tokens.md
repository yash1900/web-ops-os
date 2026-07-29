# Web-Ops OS Design System Tokens & Guidelines

## 1. Responsive & Layout Safeguards
- **Max Width Bounds:** Always use `w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8` for outer container wrappers.
- **Horizontal Overflow Prevention:** Container elements must use `overflow-x-hidden` or `max-w-full`.
- **Flex Child Sizing:** Grid and Flex children must include `min-w-0` to prevent text-node flex-grow overflows.

## 2. Color System Standards (HSL tailored)
- Dark Mode Background: `hsl(222, 47%, 11%)` (`#0f172a`)
- Card Glassmorphism Overlay: `rgba(255, 255, 255, 0.05)` backdrop-blur-md
- Primary Accent: `hsl(217, 91%, 60%)` (`#3b82f6`)

## 3. Animation Safety Rules
- WebGL & Three.js Canvas render loops must pause on tab hide: `document.addEventListener('visibilitychange', ...)`
- CSS transitions must target explicit properties (`transition-color, transform`) rather than `transition-all`.
