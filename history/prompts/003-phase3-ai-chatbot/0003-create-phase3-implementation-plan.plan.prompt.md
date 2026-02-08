---
id: "0003"
title: "Create Phase 3 Implementation Plan"
stage: plan
date: 2026-02-08
surface: agent
model: claude-opus-4-6
feature: 003-phase3-ai-chatbot
branch: 003-phase3-ai-chatbot
user: amna
command: /sp.plan
labels: ["architecture", "ai-chatbot", "openai-agents-sdk", "implementation-plan", "phase3"]
links:
  spec: specs/003-phase3-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-phase3-ai-chatbot/plan.md
  - specs/003-phase3-ai-chatbot/research.md
  - specs/003-phase3-ai-chatbot/data-model.md
  - specs/003-phase3-ai-chatbot/quickstart.md
  - specs/003-phase3-ai-chatbot/contracts/chat-api.yaml
tests:
  - null
---

## Prompt

/sp.plan — Create implementation plan for Phase 3 AI Chatbot with architecture overview, implementation phases, component breakdown, dependencies & sequencing, and key design decisions. Architecture: Frontend (ChatKit UI) → FastAPI Chat Endpoint → OpenAI Agents SDK → MCP Server → Neon PostgreSQL. Phases: Research → Foundation → Analysis → Synthesis.

## Response snapshot

Created comprehensive implementation plan with 5 artifacts:
1. **plan.md**: 7 implementation phases (A-G), constitution check (all PASS), project structure, key decisions, risks
2. **research.md**: 6 technology decisions with rationale and alternatives — notably decided to use OpenAI Agents SDK `@function_tool` directly instead of separate MCP server (simpler, sufficient for single-client use)
3. **data-model.md**: Conversation and Message entities with ER diagram, state transitions, migration notes
4. **contracts/chat-api.yaml**: OpenAPI 3.0 contract for POST /api/chat and GET /api/chat/history
5. **quickstart.md**: Developer setup guide with new files list and verification steps

Key architectural decisions: OpenAI Agents SDK over raw API, no MCP server (deferred), callback prop for dashboard refresh, custom UI components over ChatKit.

## Outcome

- Impact: Full architecture plan for Phase 3. 7 phases with clear dependency chain. 5 new backend files, 7 new frontend files, 3 modified files.
- Tests: N/A (planning phase)
- Files: 5 artifacts created
- Next prompts: /sp.tasks to generate implementation tasks
- Reflection: Research revealed that "ChatKit" is not an installable library (it's OpenAI's internal playground UI) and MCP adds unnecessary overhead for a single-client use case. Simplified architecture to use @function_tool directly.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Constitution check PASS (8/8 principles), Phase III standards PASS (4/4)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
