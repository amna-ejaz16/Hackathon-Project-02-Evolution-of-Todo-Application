# Debugging Guide: Context Preservation Fix

**Purpose**: How to verify the delete context preservation fix is working
**Audience**: Developers, QA, DevOps
**Updated**: 2026-02-11

---

## Quick Verification (5 minutes)

### Step 1: Check Backend Logs for State Machine

**What to look for**:
```
[PENDING ACTION STATE MACHINE] Entering pending action handler
[PENDING ACTION STATE MACHINE] Found pending action in metadata
[PENDING ACTION STATE MACHINE] User confirmed delete
[PENDING ACTION] Successfully deleted task_id=XXX
```

**If you see these**: ✅ Fix is working

**If you don't see these**: ❌ Issue still exists - see troubleshooting below

### Step 2: Check Browser Console

**What to look for**:
- ❌ Should NOT see: `Unable to add filesystem: <illegal path>`
- ❌ Should NOT see: MCP errors

**If console is clean**: ✅ Fix is working

**If you see errors**: ❌ MCP suppression not working - see troubleshooting below

### Step 3: Test Deletion Flow

**Steps**:
1. Open chat
2. Create a task: "create test task"
3. Say: "delete test"
4. Bot should ask: "Are you sure?"
5. Say: "yes"
6. Bot should confirm: "✓ Deleted task..."
7. Task list should refresh

**If all steps work**: ✅ Fix is working

**If step 6 fails**: ❌ Issue still exists

---

## Detailed Verification

### Verify Pending Action Detection

**Log Pattern to Find**:
```
[PENDING ACTION] Detected deletion confirmation request: task_id=5, title='coffee task', phrase_pattern_matched=True
```

**What It Means**:
- Bot found "Are you sure you want to delete" phrase
- Bot extracted task ID from "(ID: 5)"
- Pending action stored in metadata

**If Not Found**:
1. Check agent response includes "(ID: X)" format
2. Check response includes "Are you sure" or similar phrase
3. See "Pending Action Detection Patterns" section below

---

### Verify Metadata Storage

**Log Pattern to Find**:
```
[MESSAGE STORAGE] Stored assistant message message_id=123, action=conversation, pending_action={type: delete_task, ...}
```

**What It Means**:
- Message stored with pending_action in metadata
- State machine can retrieve it on next turn

**If Not Found**:
1. Check set_metadata() is called with pending_action dict
2. Check message is committed to database
3. See "Database Transaction" section below

---

### Verify Context Retrieval on Confirmation

**Log Pattern to Find**:
```
[PENDING ACTION STATE MACHINE] Found pending action in metadata: {type: delete_task, task_id: 5, ...}
[PENDING ACTION STATE MACHINE] User confirmed delete for task_id=5, title='coffee task'
[PENDING ACTION] Delete tool result: "Deleted task 'coffee task' (ID: 5)"
[PENDING ACTION] Successfully deleted task_id=5, title='coffee task'
```

**What It Means**:
- Pending action retrieved from metadata ✅
- User confirmation detected ✅
- Delete tool executed successfully ✅
- Task actually deleted from database ✅

**If Not Found**:
1. Check last assistant message retrieval
2. Check metadata.get("pending_action") works
3. Check confirmation patterns ("yes", "confirm", etc.)
4. See "Confirmation Detection" section below

---

## Log Analysis by Scenario

### Scenario 1: Successful Delete ✅

**Expected Logs**:
```
Turn 1:
[AGENT EXECUTION] Running agent with list_tasks tool
[TOOL CALL TRACKING] AI tool call: tool=list_tasks, ...
[PENDING ACTION] Detected deletion confirmation request: task_id=5, title='coffee task'
[ACTION DETECTION] Detected action=conversation (list_tasks doesn't change action)
[MESSAGE STORAGE] Stored assistant message with pending_action in metadata

Turn 2:
[PENDING ACTION STATE MACHINE] Entering pending action handler
[PENDING ACTION STATE MACHINE] Found pending action in metadata
[PENDING ACTION STATE MACHINE] User confirmed delete for task_id=5
[PENDING ACTION] Delete tool result: "Deleted task 'coffee task' (ID: 5)"
[PENDING ACTION] Successfully deleted task_id=5
[MESSAGE STORAGE] Stored assistant message with action=task_deleted
[EXECUTION FLOW] Returning ChatResponse with action=task_deleted
```

### Scenario 2: Confirmation Not Detected ❌

**Symptoms**:
- User says "yes"
- Bot doesn't delete, asks again

**Look for**:
```
[PENDING ACTION STATE MACHINE] No pending action found
  └─ Agent continues normally
```

**Root Cause**:
- Pending action not stored in Turn 1
- Agent response doesn't match detection pattern

**Check**:
```
[PENDING ACTION] Detected deletion confirmation request: ...
```
If missing, pending action wasn't detected in Turn 1.

**Solution**:
1. Check bot response includes "Are you sure" phrase
2. Check bot response includes "(ID: X)" format
3. Check detection patterns in code (lines 706-758)

---

### Scenario 3: Task ID Not Validated ❌

**Symptoms**:
- User confirms deletion
- Error message: "Invalid task ID"

**Look for**:
```
[PENDING ACTION] Invalid task_id type: str (expected int)
[PENDING ACTION] Invalid task_id value: 0 (expected > 0)
```

**Root Cause**:
- task_id corrupted in metadata
- task_id extracted incorrectly

**Check**:
1. Metadata contains valid integer task_id
2. Regex extraction works: `r'\(ID:\s*(\d+)\)'`

---

### Scenario 4: Tool Not Found ❌

**Symptoms**:
- User confirms deletion
- Error: "Task deletion tool unavailable"

**Look for**:
```
[PENDING ACTION] delete_task tool not found
```

**Root Cause**:
- Task tools not created
- delete_task tool missing from list

**Check**:
```
[AGENT EXECUTION] Created X task tools for user_id=...
[AGENT EXECUTION] Available tools: [add_task, list_tasks, complete_task, delete_task, ...]
```
If delete_task missing, check create_task_tools() function.

---

### Scenario 5: MCP Filesystem Error ❌

**Symptoms**:
- Browser console shows: `Unable to add filesystem: <illegal path>`
- Backend logs: `ROLLBACK`

**Look for**:
```
[AGENT EXECUTION] MCP error during agent init (suppressed)
```

**Why It Happens**:
- OpenAI Agents SDK tries to initialize MCP
- MCP tries to access filesystem at invalid path
- Error is suppressed but logged

**Expected Behavior**:
- Error is suppressed silently
- Agent initialization continues
- Pending action handler still works
- User doesn't see error

**If User Sees Error**:
1. stderr/stdout suppression not working
2. Check `sys.stderr = StringIO()`
3. Check `sys.stdout = StringIO()`
4. Check both are restored in finally block

---

## Common Issues and Solutions

### Issue 1: "Unable to add filesystem" in Console

**Cause**: MCP initialization error visible to user

**Solution**:
```python
# Make sure this is in place (lines 629-697):
sys.stderr = StringIO()
sys.stdout = StringIO()
try:
    agent = Agent(...)
except:
    pass
finally:
    sys.stderr = old_stderr
    sys.stdout = old_stdout
```

**Verify**: Browser console should be clean after fix

---

### Issue 2: Pending Action Not Stored

**Cause**: Detection patterns don't match bot response

**Solution**: Update detection patterns (lines 706-758)

```python
delete_confirmation_patterns = [
    r"Are you sure you want to delete",
    r"Do you want to delete",
    r"Should I delete",
    # Add custom patterns if needed
]
```

**How to Debug**:
1. Note exact bot response
2. Test regex pattern: `re.search(pattern, bot_response)`
3. If not matching, add new pattern

---

### Issue 3: Task ID Not Extracted

**Cause**: Regex pattern doesn't match bot format

**Solution**: Update ID extraction patterns (lines 711-718)

```python
id_patterns = [
    r'\(ID:\s*(\d+)\)',  # (ID: 42)
    r'ID[:\s]+(\d+)',     # ID: 42
    r'#(\d+)',            # #42
    # Add custom patterns if needed
]
```

**How to Debug**:
1. Note exact format in bot response
2. Test regex: `re.search(pattern, bot_response)`
3. If not matching, add new pattern

---

### Issue 4: Database Not Committing

**Cause**: Transaction not committed in delete_task tool

**Verify in task_tools.py** (line 291):
```python
session.delete(task)
session.commit()  # ← Must be here
```

**Check Logs**:
```
sqlalchemy.engine.Engine ROLLBACK
```
If you see ROLLBACK, transaction is failing. Check:
1. User ownership check (user_id)
2. Task exists (not already deleted)
3. No constraint violations

---

### Issue 5: Confirmation Not Detected

**Cause**: User message doesn't match confirmation patterns

**Confirmation Patterns** (lines 39-46):
```python
AFFIRMATIVE_PATTERNS = {
    "yes", "confirm", "ok", "sure", "yeah", "yep",
    "proceed", "delete it", "go ahead", "do it"
}
```

**How to Debug**:
```python
# In code:
normalized = user_message.lower().strip().strip('.,!?')
# Check if normalized is in AFFIRMATIVE_PATTERNS
```

**Common Issues**:
- Extra words: "yes please" → doesn't match (needs exact word)
- Capitalization: "Yes" → works (lowercase first)
- Punctuation: "yes!" → works (stripped)

---

## Production Monitoring

### Key Metrics

**1. Delete Success Rate**
```
[PENDING ACTION] Successfully deleted task_id=XXX  → +1 success
[PENDING ACTION] Failed to delete task_id=XXX      → +1 failure
```

**Expected**: 99%+ success rate after fix

**2. Context Loss Rate**
```
[PENDING ACTION STATE MACHINE] No pending action found → +1 context loss
```

**Expected**: 0% (all confirmations should find pending action)

**3. MCP Error Rate**
```
[AGENT EXECUTION] MCP initialization error → +1 mcp_error
```

**Expected**: Should be low/zero (suppressed anyway)

### Alerts to Set Up

**Alert 1: High Delete Failure Rate**
```
If [PENDING ACTION] Failed to delete rate > 5% in 5 minutes
→ Investigate database issues
```

**Alert 2: Context Loss Rate**
```
If [No pending action found] rate > 1% in 5 minutes
→ Check pending action detection patterns
```

**Alert 3: MCP Errors**
```
If [MCP initialization error] rate > 10% in 5 minutes
→ Check OpenAI SDK version or configuration
```

---

## Step-by-Step Debugging

### When: Task not deleted after user confirms

**Step 1**: Check backend logs for state machine entry
```bash
grep "\[PENDING ACTION STATE MACHINE\]" backend.log | tail -20
```

**Expected**: Should see "Entering pending action handler" for each confirmation

**If Missing**: Pending action handler not being called
- Check: `handle_pending_action()` called in `process_message()`
- Line: Should be ~577 in chat_service.py

---

**Step 2**: Check if pending action detected in Turn 1
```bash
grep "\[PENDING ACTION\] Detected" backend.log | tail -20
```

**Expected**: Should see detection on first user message

**If Missing**: Pending action not detected
- Check: Bot response includes "Are you sure"
- Check: Bot response includes "(ID: X)"
- Check: Detection patterns (lines 706-758)

---

**Step 3**: Check if metadata stored
```bash
grep "pending_action" backend.log | tail -20
```

**Expected**: Should see pending_action in metadata

**If Missing**: Not storing pending action
- Check: `metadata["pending_action"] = {}`
- Check: Message committed to database

---

**Step 4**: Check if context retrieved on Turn 2
```bash
grep "\[PENDING ACTION STATE MACHINE\] Found pending action" backend.log | tail -20
```

**Expected**: Should find pending action from last message

**If Missing**: Metadata not being retrieved
- Check: Last assistant message found
- Check: metadata.get() works
- Check: Database query returns message

---

**Step 5**: Check if delete executed
```bash
grep "\[PENDING ACTION\] Delete tool result" backend.log | tail -20
```

**Expected**: Should see delete tool output

**If Missing**: Delete tool not called
- Check: Tool validation passes (task_id valid)
- Check: delete_task tool found in tools list
- Check: Tool execution completed

---

**Step 6**: Check browser console
```javascript
// In F12 console:
// Should NOT see "Unable to add filesystem"
// Should see chat messages normally
```

**If Errors**: MCP suppression not working
- Check: stderr/stdout being captured
- Check: finally block restoring streams

---

## Log File Locations

**Backend Logs**:
```
Docker: /var/log/app/backend.log
Development: stdout/stderr from `python -m uvicorn ...`
```

**Frontend Logs**:
```
Browser: Press F12 → Console tab
Local Storage: DevTools → Application → Local Storage
```

**Database Logs**:
```
SQLite: In-memory (development)
PostgreSQL: Usually /var/log/postgresql/
```

---

## Testing Checklist

- [ ] Task deletion works (happy path)
- [ ] Cancellation works ("no" response)
- [ ] No console errors visible
- [ ] Backend logs show state machine transitions
- [ ] Create/Update/Complete features still work
- [ ] Multiple deletions in sequence work
- [ ] Different confirmation phrases work ("yes", "ok", "confirm")
- [ ] Invalid task IDs handled gracefully
- [ ] Database transactions complete (no rollbacks)

---

## Quick Reference: Key Code Locations

| What | File | Line | What to Check |
|-----|------|------|---------------|
| Pending action check | chat_service.py | 576-586 | Called before agent init |
| Pending action handler | chat_service.py | 233-414 | State machine logic |
| Pending action detection | chat_service.py | 706-758 | Detection patterns |
| Tool call tracking | chat_service.py | 773-806 | Action detection |
| Delete tool | task_tools.py | 269-299 | Tool implementation |
| Confirmation patterns | chat_service.py | 39-59 | "yes"/"no" detection |

---

## When to Use This Guide

1. **After Deployment**: Verify fix is working
2. **When Debugging**: Use logs to identify issue
3. **When Testing**: Follow checklist
4. **When Monitoring**: Set up metrics/alerts

---

**Status**: Reference document for verification and debugging
**Last Updated**: 2026-02-11
