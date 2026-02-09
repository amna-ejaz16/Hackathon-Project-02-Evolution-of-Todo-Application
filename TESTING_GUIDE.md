# Phase 3 AI Chatbot - Local Testing Guide

## Prerequisites

Before running local tests, ensure you have:
- Python 3.11+ (backend)
- Node.js 20+ (frontend)
- PostgreSQL database (Neon or local)
- OpenAI API key (for AI chat features)
- Better Auth secret (32+ characters)

## Setup Instructions

### 1. Backend Setup

```bash
cd backend

# Create .env file from example
cp .env.example .env

# Edit .env with your credentials:
# - DATABASE_URL: Your Neon PostgreSQL connection string
# - OPENAI_API_KEY: Your OpenAI API key (sk-...)
# - BETTER_AUTH_SECRET: Your 32+ character secret

# Install dependencies
pip install -r requirements.txt

# Run database migrations (creates tables)
python -m src.core.database
# or via API startup (tables auto-created on first run)

# Start backend server (port 8000)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local if needed (inherits from .env files)
# Frontend uses existing auth and API configuration

# Start development server (port 3000)
npm run dev
```

**Expected Output:**
```
  ▲ Next.js 16.0.0
  - Local:        http://localhost:3000
  - Environments: .env.local

✓ Ready in 2.3s
```

### 3. Verify Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Database Health**: `POST /api/health` should return `{"status": "healthy"}`

## Testing Workflow (Quickstart)

Follow these 6 steps from `specs/003-phase3-ai-chatbot/quickstart.md`:

### Step 1: Open Dashboard
1. Navigate to http://localhost:3000
2. Sign up with test email/password or log in
3. Verify dashboard loads with task list

**Expected Result:** Dashboard visible with task creation form and chat FAB

### Step 2: Click FAB to Open Chat
1. Look for purple/pink gradient circular button (💬) at bottom-right
2. Click the FAB
3. Verify chat panel slides in

**Expected Result:** Chat panel opens smoothly from right side on desktop, or bottom-up on mobile

### Step 3: Send "Show all my tasks" Message
1. Click in message input field
2. Type: `Show all my tasks`
3. Press Enter or click send button
4. Verify typing indicator (3 pulsing dots) appears

**Expected Result:**
- User message appears right-aligned in purple gradient
- Typing indicator shows for 1-3 seconds
- AI responds with task list or "You don't have any tasks yet"

### Step 4: Verify AI Response Format
1. Check AI response displays as left-aligned glass bubble
2. Verify message includes: title, status (✓/○), priority (🔴/🟡/🟢), due date
3. Messages auto-scroll to bottom

**Expected Result:** Properly formatted task list with all details visible

### Step 5: Create Task via Chat
1. Type: `Add a task to test the chatbot with high priority`
2. Press Enter
3. Verify:
   - User message appears in chat
   - Typing indicator shows
   - AI creates the task and confirms

**Expected Result:**
- AI responds: "Created task 'test the chatbot' (ID: X) with priority high..."
- Dashboard task list auto-refreshes with new task visible

### Step 6: Verify Dashboard Update
1. Close chat panel (click X or press ESC)
2. Look at task list on dashboard
3. Verify new task appears in the list

**Expected Result:** New task visible with correct title, priority, and created timestamp

## Advanced Testing Scenarios

### Test Quick Action Pills
1. Open chat panel
2. Verify 3 pills appear below messages:
   - "Show all tasks"
   - "Add a task"
   - "What's overdue?"
3. Click "Show all tasks" pill
4. Verify message sent automatically

**Expected Result:** Quick action triggers message send without manual typing

### Test List Filtering
Send these commands and verify filtering works:
1. `Show me pending tasks` → Only incomplete tasks
2. `Show high priority tasks` → Only high priority
3. `What are my work tasks?` → Only category="Work" (if any)

**Expected Result:** AI filters results correctly per query

### Test Task Operations
Try these commands:
1. **Create**: `Add task: Lunch at noon, medium priority, due tomorrow`
2. **Complete**: `Mark the lunch task as complete`
3. **Update**: `Change lunch priority to high`
4. **Delete**: `Delete the lunch task` (AI should ask for confirmation)

**Expected Result:** Each operation succeeds with AI confirmation and dashboard updates

### Test Error Scenarios

**Scenario 1: Missing OpenAI Key**
- Remove OPENAI_API_KEY from .env
- Restart backend
- Try to send message
- Expected: HTTP 503 "AI service temporarily unavailable"
- Chat displays: "I'm having trouble connecting right now..."

**Scenario 2: Network Error**
- Close backend server
- Try to send message from frontend
- Expected: HTTP error or no response
- Chat displays: "Connection lost. Please check your internet..."

**Scenario 3: Session Expired**
- Manually expire JWT token (edit browser storage)
- Try to send message
- Expected: HTTP 401 Unauthorized
- Chat displays: "Session expired, please refresh the page"

### Test History Persistence
1. Open chat and send 5 messages
2. Close chat panel
3. Reopen chat panel
4. Verify all 5 messages still visible
5. Refresh page
6. Reopen chat
7. Verify messages persist after page reload

**Expected Result:** History loads on panel open and persists across sessions

### Test Mobile Behavior
1. Open http://localhost:3000 on mobile device or use DevTools device emulation
2. Tap FAB at bottom
3. Verify chat opens as full-width bottom sheet
4. Drag header down to close
5. Verify smooth dismiss animation

**Expected Result:** Mobile bottom sheet opens from bottom, dismisses on drag

### Test Message Length
1. Send very long message (>500 chars)
2. Verify it wraps properly in bubble
3. Send message with special characters (emoji, symbols)
4. Verify they render correctly

**Expected Result:** No text overflow, proper rendering

## Expected Chat Features

### When Working Correctly:
✅ Chat FAB visible and clickable on dashboard
✅ Panel opens/closes with smooth animation
✅ Messages send and receive properly
✅ Typing indicator appears while AI processes
✅ Auto-scroll to latest message
✅ Quick action pills work
✅ Dashboard refreshes on task mutations
✅ History loads on panel open
✅ Welcome message shown on first open
✅ Error messages display gracefully
✅ Mobile bottom sheet works

### Tools Available to AI:
- `list_tasks` - List all/filtered tasks
- `add_task` - Create new task
- `update_task` - Modify task fields
- `complete_task` - Mark complete
- `uncomplete_task` - Mark incomplete
- `delete_task` - Remove task

## Debugging

### Check Backend Logs
```bash
# Logs show:
# [CONVERSATION LIFECYCLE] - Message processing flow
# [MESSAGE STORAGE] - Message save operations
# [AGENT EXECUTION] - AI agent execution
# [TOOL CALL TRACKING] - Which AI tools were called
# [ACTION DETECTION] - What action was detected
```

### Check Frontend Network
1. Open DevTools → Network tab
2. Look for:
   - `POST /api/chat` - Message send (should return ChatResponse)
   - `GET /api/chat/history` - History load (should return ChatHistoryResponse)
3. Check response status: 200 (success), 503 (unavailable), 401 (unauthorized)

### Check Database
```bash
# Connect to Neon PostgreSQL
psql <your-neon-connection-string>

# Verify tables exist
\dt
# Should show: conversation, message, task, user, etc.

# Check chat data
SELECT id, user_id, title, created_at FROM conversation LIMIT 5;
SELECT id, conversation_id, role, content FROM message ORDER BY created_at DESC LIMIT 10;
```

## Common Issues & Solutions

### Issue: "OPENAI_API_KEY not set"
**Solution:**
- Check .env file has OPENAI_API_KEY=sk-...
- Restart backend server after updating .env
- Verify key is valid (starts with sk-)

### Issue: Chat sends message but no response
**Solution:**
- Check backend logs for [AGENT EXECUTION] errors
- Verify OpenAI API key is valid
- Check network tab for 503 status (service unavailable)
- Check database connectivity (DATABASE_URL valid)

### Issue: Dashboard doesn't refresh after chat task creation
**Solution:**
- Check ChatWidget has `onTaskChange={fetchTasks}` prop
- Verify ChatResponse includes `action="task_created"`
- Check frontend console for errors
- Manually refresh page (Ctrl+R)

### Issue: History doesn't load when panel opens
**Solution:**
- Check `GET /api/chat/history` in network tab
- Verify response includes messages array
- Check that conversation exists in database
- Check localStorage doesn't block API calls

### Issue: Mobile chat doesn't dismiss on drag
**Solution:**
- Ensure you're dragging on the header area (dark top bar)
- Drag distance must be >100px
- Drag velocity must be significant (>500px/s)
- Check Framer Motion is loaded (no console errors)

## Performance Expectations

- **Chat panel open**: <100ms
- **Message send/receive**: 1-5 seconds (depends on OpenAI API)
- **History load**: <500ms
- **Dashboard refresh**: <100ms
- **Message display**: Instant (no visible lag)

## Files to Monitor

When testing, monitor these files for logging:
- **Backend**: `backend/src/services/chat_service.py` (logs tool calls, actions)
- **Frontend**: Browser DevTools Console (API errors, component logs)
- **Database**: PostgreSQL logs (query execution)

## Completion Criteria

Test is complete when:
1. ✅ All 6 quickstart steps pass
2. ✅ Chat FAB visible and functional
3. ✅ Messages send and receive without errors
4. ✅ Typing indicator shows during AI processing
5. ✅ Dashboard refreshes on task operations
6. ✅ History persists after panel close/reopen
7. ✅ Error states handled gracefully
8. ✅ Mobile bottom sheet works
9. ✅ All 6 AI tools work (list, create, complete, uncomplete, delete, update)
10. ✅ No console errors in browser or backend

## Next Steps After Testing

Once local testing passes:
1. Run linting and type checks: `npm run type-check` (frontend), `pyright` (backend)
2. Document any issues found
3. Create commit with test results
4. Ready for GitHub push and deployment

## Support

For issues not listed above:
1. Check backend logs for errors: `grep ERROR backend.log`
2. Check frontend console: DevTools → Console tab
3. Verify .env variables are set: `cat backend/.env`
4. Check database connection: `psql <DATABASE_URL>`
5. Verify OpenAI API key works: `curl -H "Authorization: Bearer sk-..." https://api.openai.com/v1/models`
