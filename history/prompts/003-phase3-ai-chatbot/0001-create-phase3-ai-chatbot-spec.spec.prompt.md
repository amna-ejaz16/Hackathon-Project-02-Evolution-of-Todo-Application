---
id: "0001"
title: "Create Phase 3 AI Chatbot Spec"
stage: spec
date: 2026-02-08
surface: agent
model: claude-opus-4-6
feature: 003-phase3-ai-chatbot
branch: 003-phase3-ai-chatbot
user: amna
command: /sp.specify
labels: ["ai-chatbot", "cyberpunk-ui", "mcp-tools", "phase3", "specification"]
links:
  spec: specs/003-phase3-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-phase3-ai-chatbot/spec.md
  - specs/003-phase3-ai-chatbot/checklists/requirements.md
tests:
  - null
---

## Prompt

Todo AI Chatbot – Cyberpunk UI/UX

Target Audience: Dashboard users and developers enhancing UI/UX

Objective: Floating AI assistant to manage tasks via natural language using MCP tools; fully UI/UX focused, cyberpunk theme, maintain existing backend functionality

Success Criteria:
Functional AI chat panel with FAB entry
All basic task operations via MCP (add, list, complete, delete, update)
Smooth Framer Motion animations
Responsive layout: desktop panel + mobile bottom sheet
Visual consistency with cyberpunk dashboard theme

Constraints:
UI/UX only: modify JSX, Tailwind CSS, Framer Motion, layout
Do not touch backend, auth, API, session, routing, or todo logic
Maintain existing functionality and design consistency

1. Placement & Entry: FAB bottom-right, neon gradient, hover lift. Opens chat panel; transforms to close.
2. Chat Panel Layout: Desktop side panel (~350-400px, 500-600px). Mobile full-width bottom sheet. Glassmorphism.
3. Components: Header with AI avatar, title, close button. Scrollable messages. Typing indicator. Input with send button. Quick action pills.
4. Animations: Framer Motion for FAB hover, panel slide, message entrance, typing indicator.
5. Visual Consistency: Cyberpunk dark theme, neon purple/magenta, glassmorphism, rounded edges.
6. Responsiveness: Desktop floating side panel. Mobile bottom sheet with swipe dismiss.
7. AI Chatbot Functionality: ChatKit frontend, FastAPI + OpenAI Agents SDK backend, MCP server task tools, Neon PostgreSQL.
8. Conversation Flow: Receive message, fetch history, build context, store messages, run agent with MCP tools, return response.
9. Natural Language Commands: add_task, list_tasks, complete_task, delete_task, update_task mapped from natural language.

## Response snapshot

Created comprehensive specification at `specs/003-phase3-ai-chatbot/spec.md` with 8 user stories (P1: chat widget + messaging + task creation; P2: list/complete/delete/update; P3: quick action pills + conversation persistence), 24 functional requirements, 6 non-functional requirements, 10 measurable success criteria, 6 edge cases, and documented assumptions. Quality checklist at `specs/003-phase3-ai-chatbot/checklists/requirements.md` passes all validation items.

## Outcome

- Impact: Feature specification created for Phase 3 AI chatbot integration. Covers full CRUD via natural language, cyberpunk UI/UX, responsive design, and conversation persistence.
- Tests: N/A (specification phase - no code)
- Files: 2 files created (spec.md, checklists/requirements.md)
- Next prompts: /sp.clarify to validate spec gaps, then /sp.plan for architecture
- Reflection: Balanced user's constraint ("UI/UX only, don't touch backend") with reality that chatbot requires backend work. Spec treats existing backend as immutable but allows new chat-specific additions alongside.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Spec quality checklist PASS (all items)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
