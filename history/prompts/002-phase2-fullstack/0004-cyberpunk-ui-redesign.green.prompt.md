---
id: 0004
title: Cyberpunk UI Redesign with Framer Motion
stage: green
date: 2026-01-31
surface: agent
model: claude-opus-4-5-20251101
feature: 002-phase2-fullstack
branch: 002-phase2-fullstack
user: amna_linux166
command: UI redesign request
labels: ["ui", "tailwind", "framer-motion", "dark-theme", "cyberpunk"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/package.json
  - frontend/tailwind.config.ts
  - frontend/src/app/globals.css
  - frontend/src/app/layout.tsx
  - frontend/src/app/(auth)/signup/SignupForm.tsx
  - frontend/src/app/(auth)/signin/SigninForm.tsx
  - frontend/src/app/dashboard/DashboardClient.tsx
tests:
  - null
---

## Prompt

UI UPDATE ONLY — DO NOT CHANGE ANY LOGIC, AUTH FLOW, API CALLS, STATE MANAGEMENT, OR DATABASE CODE.
I want you to only update the UI (design + animations) of my existing app using Tailwind CSS and Framer Motion, while keeping all existing functionality exactly the same.

Global Rules:
- Do NOT modify authentication logic, redirects, API calls, middleware, guards, or session handling
- Do NOT change form handlers, submit logic, or backend integration
- Do NOT rename routes, components, or variables used in logic
- ONLY update JSX structure, Tailwind classes, visual components, and Framer Motion animations

Requirements:
1. Sign Up Page UI - Centered layout, App name "Task Manager" with tick logo, heading "Create Account", neon purple/magenta gradient button
2. Sign In Page UI - Same styling as Sign Up
3. Dashboard UI - Cyberpunk dark theme with neon purple/magenta accents, glassmorphism, glowing gradient cards
4. Navbar - Logo + Task Manager on left, Sign In/Out button on right
5. Hero Section - Quote "Organize your chaos. One task at a time." with Framer Motion animation
6. Feature Cards - 3 cards (Smart Task Management, Boost Productivity, Secure & Personal) with hover effects

## Response snapshot

Completed a comprehensive UI redesign with cyberpunk dark theme:

1. Added `framer-motion` package for animations
2. Extended Tailwind config with custom neon colors, gradients, shadows, and animations
3. Created glassmorphism utilities and dark theme components in globals.css
4. Updated root layout for dark mode
5. Redesigned SignupForm and SigninForm with:
   - Task Manager branding + tick/checkmark logo
   - Neon gradient buttons with glow effects
   - Dark themed inputs with focus glow
   - Framer Motion entrance animations
6. Completely redesigned DashboardClient with:
   - Sticky glassmorphism navbar
   - Animated hero section with quote
   - 3 feature cards with hover animations
   - Dark themed task cards with neon accents
   - Custom checkbox styling
   - AnimatePresence for smooth transitions

All logic, API calls, authentication, state management, and form handlers preserved unchanged.

## Outcome

- ✅ Impact: Complete visual transformation to cyberpunk dark theme while preserving all functionality
- 🧪 Tests: Manual visual testing required - run `npm run dev` in frontend directory
- 📁 Files: 7 files modified (package.json, tailwind.config.ts, globals.css, layout.tsx, SignupForm.tsx, SigninForm.tsx, DashboardClient.tsx)
- 🔁 Next prompts: Test the app visually, adjust colors/animations if needed
- 🧠 Reflection: Successfully separated UI concerns from logic concerns - no authentication or API code was touched

## Evaluation notes (flywheel)

- Failure modes observed: None - strict UI-only changes maintained
- Graders run and results (PASS/FAIL): N/A - visual changes require manual review
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Fine-tune animation timings or add additional micro-interactions
