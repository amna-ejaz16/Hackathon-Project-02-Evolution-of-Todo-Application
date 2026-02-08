# Feature Specification: Todo AI Chatbot - Cyberpunk UI/UX

**Feature Branch**: `003-phase3-ai-chatbot`
**Created**: 2026-02-08
**Status**: Draft
**Input**: User description: "Floating AI assistant to manage tasks via natural language using MCP tools; cyberpunk theme, maintain existing backend functionality"

## Clarifications

### Session 2026-02-08

- Q: When a task is created, completed, updated, or deleted via the chat, should the dashboard task list auto-refresh? → A: Yes, auto-refresh the dashboard task list after each successful chat task operation.
- Q: How many previous messages should be included as AI context for multi-turn dialogue? → A: Last 20 messages (sliding window).
- Q: Should there be a maximum number of stored messages per user conversation? → A: Yes, 200 messages max per conversation; oldest messages pruned automatically when cap reached.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Open and Close the AI Chat Widget (Priority: P1)

A logged-in user on the dashboard sees a floating action button (FAB) in the bottom-right corner. Clicking it opens a chat panel where they can interact with the AI assistant. Clicking again (or a close button) dismisses the panel. The FAB and panel have cyberpunk-themed styling consistent with the existing dashboard.

**Why this priority**: The chat widget is the entry point for all AI interactions. Without it, no other chatbot feature is accessible. This is the foundation.

**Independent Test**: Can be fully tested by verifying the FAB renders on the dashboard, opens a panel on click, and closes on dismiss. Delivers value as a visible, interactive UI element.

**Acceptance Scenarios**:

1. **Given** a logged-in user on the dashboard, **When** the page loads, **Then** a circular FAB with neon purple-to-magenta gradient appears in the bottom-right corner with a soft glow effect.
2. **Given** the FAB is visible, **When** the user clicks it, **Then** a chat panel slides open with smooth animation and the FAB transforms into a close button.
3. **Given** the chat panel is open, **When** the user clicks the close button, **Then** the panel slides closed with smooth animation and the FAB reappears.
4. **Given** a mobile viewport (< 768px), **When** the user opens the chat, **Then** the panel appears as a full-width bottom sheet instead of a side panel.
5. **Given** the chat panel is open on mobile, **When** the user swipes down on the panel header, **Then** the panel dismisses.

---

### User Story 2 - Send a Message and Receive AI Response (Priority: P1)

A user types a natural language message into the chat input field and sends it. The message appears in the chat as a user bubble (right-aligned, neon-styled). A typing indicator appears while the AI processes. The AI response appears as an assistant bubble (left-aligned, glass-styled) with a fade-and-slide entrance animation.

**Why this priority**: Core chat interaction is essential for all task management via natural language. This enables the fundamental send/receive loop.

**Independent Test**: Can be tested by typing any message, sending it, and verifying the message renders correctly, a typing indicator shows, and a response appears.

**Acceptance Scenarios**:

1. **Given** the chat panel is open, **When** the user types a message and presses Enter (or clicks send), **Then** the message appears as a right-aligned bubble with neon styling.
2. **Given** a message has been sent, **When** the AI is processing, **Then** an animated typing indicator (pulsing dots) appears in the message area.
3. **Given** the AI has finished processing, **When** the response is ready, **Then** it appears as a left-aligned bubble with glassmorphism styling and a fade+slide entrance animation.
4. **Given** the input field is empty, **When** the user presses Enter or clicks send, **Then** nothing happens (no empty messages sent).
5. **Given** multiple messages have been exchanged, **When** a new message appears, **Then** the message area auto-scrolls to the latest message.

---

### User Story 3 - Create a Task via Chat (Priority: P1)

A user types a natural language command like "Add a task to buy groceries by Friday with high priority" and the AI assistant creates the task, confirms the action with details, and the task appears in the dashboard task list.

**Why this priority**: Task creation via natural language is the primary value proposition of the chatbot. It demonstrates the AI can perform real actions.

**Independent Test**: Can be tested by sending a create-task command, verifying the AI confirms creation, and checking the task appears in the dashboard list.

**Acceptance Scenarios**:

1. **Given** the chat is open, **When** the user says "Add a task to buy groceries by Friday with high priority", **Then** the AI creates the task and responds with a confirmation message including the task details (title, priority, due date).
2. **Given** a task was just created via chat, **When** the user views the dashboard task list, **Then** the new task appears with the correct details.
3. **Given** the user provides an incomplete command like "Add a task", **When** the AI processes it, **Then** the AI asks for clarification (e.g., "What should the task title be?") rather than creating a blank task.
4. **Given** the user provides a title but no other details, **When** the AI creates the task, **Then** reasonable defaults are applied (medium priority, no category, no due date) and the AI confirms what was created.

---

### User Story 4 - List and Query Tasks via Chat (Priority: P2)

A user asks the AI to show their tasks using natural language like "Show all my tasks", "What's pending?", or "Show high priority tasks". The AI responds with a formatted summary of matching tasks.

**Why this priority**: Querying tasks via chat is the second most common operation after creation. It enables users to get quick task overviews without scanning the dashboard.

**Independent Test**: Can be tested by asking the AI to list tasks and verifying the response contains accurate task data matching the dashboard.

**Acceptance Scenarios**:

1. **Given** the user has tasks, **When** they say "Show all my tasks", **Then** the AI responds with a formatted list of all tasks showing title, status, priority, and due date.
2. **Given** the user has both completed and pending tasks, **When** they say "What's pending?", **Then** the AI responds with only incomplete tasks.
3. **Given** the user says "Show high priority tasks", **When** the AI processes it, **Then** only high-priority tasks are returned.
4. **Given** the user has no tasks, **When** they ask to list tasks, **Then** the AI responds with a friendly message like "You don't have any tasks yet. Want me to create one?"

---

### User Story 5 - Complete and Delete Tasks via Chat (Priority: P2)

A user can mark tasks as complete or delete them using natural language commands. The AI confirms the action and the dashboard reflects the change.

**Why this priority**: Completing and deleting tasks are essential CRUD operations that round out the chatbot's task management capabilities.

**Independent Test**: Can be tested by completing or deleting a known task via chat and verifying the change in the dashboard.

**Acceptance Scenarios**:

1. **Given** the user has a task titled "Buy groceries", **When** they say "Complete the buy groceries task", **Then** the AI marks it as complete and confirms with the task title.
2. **Given** the user says "Delete the buy groceries task", **When** the AI processes it, **Then** the AI asks for confirmation before deleting (e.g., "Are you sure you want to delete 'Buy groceries'?").
3. **Given** the user confirms deletion, **When** the AI deletes the task, **Then** it confirms deletion and the task no longer appears in the dashboard.
4. **Given** the user references a task that doesn't exist, **When** the AI processes the command, **Then** it responds with a helpful message (e.g., "I couldn't find a task matching 'Buy groceries'. Want me to list your tasks?").
5. **Given** multiple tasks match the user's description, **When** the AI processes the command, **Then** it lists the matching tasks and asks the user to specify which one.

---

### User Story 6 - Update Tasks via Chat (Priority: P2)

A user can update task details via natural language, such as changing priority, category, due date, title, or description.

**Why this priority**: Updating tasks completes the full CRUD capability of the chatbot.

**Independent Test**: Can be tested by updating a task field via chat and verifying the change in the dashboard.

**Acceptance Scenarios**:

1. **Given** a task "Buy groceries" exists with medium priority, **When** the user says "Change buy groceries to high priority", **Then** the AI updates the priority and confirms the change.
2. **Given** a task exists, **When** the user says "Set the due date for buy groceries to next Monday", **Then** the AI updates the due date and confirms.
3. **Given** a task exists, **When** the user says "Rename buy groceries to Get weekly groceries", **Then** the AI updates the title and confirms.
4. **Given** the user provides an ambiguous update command, **When** the AI processes it, **Then** it asks for clarification rather than making incorrect changes.

---

### User Story 7 - Quick Action Pills (Priority: P3)

Below the chat input, optional quick action pills provide one-tap shortcuts for common operations like "Show all tasks", "Add a task", "What's overdue?". Tapping a pill sends the corresponding command as a chat message.

**Why this priority**: Convenience feature that improves discoverability and speed but is not essential for core functionality.

**Independent Test**: Can be tested by tapping a pill and verifying the correct command is sent as a message.

**Acceptance Scenarios**:

1. **Given** the chat panel is open, **When** the user sees the input area, **Then** quick action pills are displayed with cyberpunk styling (rounded, neon glow, hover lift).
2. **Given** quick action pills are visible, **When** the user taps "Show all tasks", **Then** the message "Show all tasks" appears as a user message and triggers the corresponding AI response.

---

### User Story 8 - Conversation History Persistence (Priority: P3)

Chat conversations are persisted per user so that when a user reopens the chat panel, previous messages are displayed. Conversations are stored in the database and scoped to the authenticated user.

**Why this priority**: Persistence improves UX but the chatbot is fully functional without it (in-session messages suffice for MVP).

**Independent Test**: Can be tested by sending messages, closing the panel, reopening it, and verifying messages persist.

**Acceptance Scenarios**:

1. **Given** the user has sent messages in a previous session, **When** they open the chat panel, **Then** previous messages are loaded and displayed.
2. **Given** conversation history exists, **When** the AI processes a new message, **Then** the conversation context includes prior messages for coherent multi-turn dialogue.
3. **Given** the user opens the chat for the first time, **When** the panel loads, **Then** a welcome message from the AI is displayed (e.g., "Hi! I'm your Task Manager Assistant. How can I help you today?").

---

### Edge Cases

- What happens when the AI service is temporarily unavailable? Display a user-friendly error in the chat (e.g., "I'm having trouble connecting. Please try again in a moment.") with a retry option.
- What happens when the user sends a message that doesn't map to any task operation? The AI responds conversationally and gently guides the user toward supported operations.
- What happens when the user sends rapid successive messages? Messages are queued and processed sequentially; the UI shows a typing indicator for each pending response.
- What happens when the JWT token expires mid-conversation? The chat displays an authentication error and prompts the user to refresh the page.
- What happens when a task operation fails (e.g., database error)? The AI communicates the failure clearly and suggests retrying.
- What happens when the chat panel is open and the user creates/modifies a task via the dashboard UI? The chat does not need to reflect this change in real-time, but the next list command should return updated data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a floating action button (FAB) on the dashboard page, positioned at the bottom-right corner, visible only to authenticated users.
- **FR-002**: System MUST open a chat panel when the FAB is clicked, with smooth slide animation (desktop: side panel ~350-400px wide, ~500-600px tall; mobile: full-width bottom sheet).
- **FR-003**: System MUST close the chat panel when the close button is clicked or (on mobile) when the user swipes down on the panel header.
- **FR-004**: System MUST display a chat header with an AI avatar/icon, title "Task Manager Assistant", and a close button with a gradient accent strip.
- **FR-005**: System MUST provide a text input field with dark glassmorphism styling, neon focus ring, and a gradient send button with hover/press states.
- **FR-006**: System MUST display user messages as right-aligned bubbles with neon styling and AI messages as left-aligned bubbles with glassmorphism styling.
- **FR-007**: System MUST show an animated typing indicator (pulsing dots) while the AI is processing a response.
- **FR-008**: System MUST apply fade and slide entrance animations to new messages using Framer Motion.
- **FR-009**: System MUST auto-scroll the message area to the latest message when new messages appear.
- **FR-010**: System MUST support creating tasks via natural language commands (e.g., "Add a task to buy groceries by Friday with high priority").
- **FR-011**: System MUST support listing/querying tasks via natural language (e.g., "Show all tasks", "What's pending?", "Show high priority tasks").
- **FR-012**: System MUST support completing tasks via natural language (e.g., "Complete the buy groceries task").
- **FR-013**: System MUST support deleting tasks via natural language with confirmation before destructive actions.
- **FR-014**: System MUST support updating task details via natural language (title, description, priority, category, due date).
- **FR-015**: System MUST authenticate chat requests using the same JWT token mechanism as existing task API endpoints.
- **FR-016**: System MUST scope all task operations to the authenticated user (no cross-user data access).
- **FR-017**: System MUST log all AI decisions and tool invocations with reasoning traces for explainability.
- **FR-018**: System MUST constrain AI responses to predefined task management intents only; no actions outside defined operations.
- **FR-019**: System MUST display quick action pills below the input area as optional shortcuts for common operations.
- **FR-020**: System MUST persist conversation history per user in the database, loading previous messages when the chat panel is reopened.
- **FR-021**: System MUST display a welcome message when a user opens the chat for the first time.
- **FR-022**: System MUST handle AI service unavailability gracefully with user-friendly error messages and retry options.
- **FR-023**: System MUST ask for clarification when user commands are ambiguous or incomplete rather than performing incorrect operations.
- **FR-024**: System MUST display disambiguation when multiple tasks match a user's reference, listing options for the user to choose from.
- **FR-025**: System MUST auto-refresh the dashboard task list after each successful task operation performed via the chat (create, complete, delete, update), so the user sees the change reflected immediately without manual page reload.
- **FR-026**: System MUST use a sliding context window of the last 20 messages (user + assistant) when sending conversation history to the AI for multi-turn dialogue coherence.
- **FR-027**: System MUST enforce a maximum of 200 stored messages per user conversation; when the cap is reached, the oldest messages MUST be pruned automatically.

### Non-Functional Requirements

- **NFR-001**: Chat panel styling MUST be visually consistent with the existing cyberpunk dashboard theme (dark background, neon purple/magenta accents, glassmorphism, soft glow, rounded edges).
- **NFR-002**: Chat panel MUST be fully responsive (desktop: floating side panel; mobile <768px: full-width bottom sheet).
- **NFR-003**: All animations MUST be subtle and performant (no jank on 60fps target).
- **NFR-004**: AI response time MUST be under 5 seconds for simple operations (create, complete, delete) under normal conditions.
- **NFR-005**: Chat MUST not interfere with existing dashboard functionality (task CRUD via UI continues to work independently).
- **NFR-006**: Existing backend task endpoints, authentication, session management, and routing MUST NOT be modified.

### Key Entities

- **Conversation**: Represents a chat session between a user and the AI assistant. Key attributes: unique identifier, associated user, creation timestamp. Each user has one active conversation. Maximum 200 messages retained; oldest pruned when cap reached.
- **Message**: A single chat message within a conversation. Key attributes: unique identifier, conversation reference, role (user or assistant), content text, timestamp, optional metadata (tool calls, reasoning traces). AI context uses a sliding window of the last 20 messages.
- **Task** *(existing)*: The existing task entity with title, description, priority, category, due date, completion status. Referenced by the AI for all task operations.

## Assumptions

- The existing dashboard page (`/dashboard`) and its `DashboardClient` component are the host for the chat widget. No new pages or routes are created.
- The AI assistant communicates only in English.
- Conversation history is per-user (one active conversation thread per user). No multi-conversation management is needed.
- The AI uses the same existing task CRUD operations internally (reuses existing business logic, does not create parallel implementations).
- Quick action pills are a static set of common commands (not AI-generated or dynamic).
- The chat panel does not need real-time synchronization with dashboard task changes; the next query reflects the latest state.
- The FAB is not shown on non-dashboard pages (signin, signup, landing).
- Mobile breakpoint for bottom-sheet behavior is 768px (standard tablet/phone breakpoint).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can open the chat widget and send their first message within 5 seconds of clicking the FAB.
- **SC-002**: 100% of supported task operations (create, list, complete, delete, update) are executable via natural language in the chat.
- **SC-003**: AI responses appear within 5 seconds for single-tool operations under normal network conditions.
- **SC-004**: Chat panel renders correctly on viewports from 320px to 2560px wide with no layout breakage.
- **SC-005**: All chat interactions are authenticated; 100% of unauthenticated chat requests are rejected.
- **SC-006**: All AI tool invocations are logged with reasoning traces; zero opaque AI actions.
- **SC-007**: Existing dashboard task CRUD (via UI) continues to function with zero regressions after chatbot integration.
- **SC-008**: Chat panel animations run at 60fps with no visible jank on mid-range devices.
- **SC-009**: The AI correctly identifies and executes the intended task operation for at least 90% of well-formed natural language commands.
- **SC-010**: Conversation history persists across panel open/close cycles for the same user session.
