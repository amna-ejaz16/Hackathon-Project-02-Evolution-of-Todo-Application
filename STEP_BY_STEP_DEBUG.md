# Step-by-Step Debug Guide: Pending Action Handler

**Objective**: Identify exactly why pending action handler is not working
**Time**: 15-20 minutes
**Prerequisites**: Access to backend terminal and browser

---

## PHASE 1: SETUP (5 minutes)

### Step 1.1: Enable Debug Logging

**In your backend main.py or startup code**, find the logging configuration and set it to INFO level:

```python
import logging

# Set root logger to INFO
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Ensure chat_service logger is at INFO level
logger = logging.getLogger("src.services.chat_service")
logger.setLevel(logging.INFO)
```

### Step 1.2: Start Backend with Logging

```bash
# Kill any existing backend process
# Then restart with visible logs

# Option A: Direct Python
cd backend
python -m uvicorn src.main:app --reload --log-level info

# Option B: Docker
docker-compose up backend --force-recreate

# You should see logs streaming in the terminal
```

### Step 1.3: Keep Two Terminal Windows Open

- **Terminal 1**: Backend logs (streaming)
- **Terminal 2**: For running curl commands or notes

---

## PHASE 2: TEST PREPARATION (2 minutes)

### Step 2.1: Clear Chat History (Optional)

Log into the app and delete your conversation, or create a fresh test conversation.

### Step 2.2: Create a Task to Delete

In the chat, say:
```
"create a task called test delete me with high priority"
```

**Expected**: Bot creates task (should show something like "task ID: 5")

**Note the task ID** - you'll need it later.

### Step 2.3: Prepare Copy/Paste Area

Have a text editor ready to paste logs into:
```
=== TURN 1: DELETE REQUEST ===
[Logs here]

=== TURN 2: YES CONFIRMATION ===
[Logs here]
```

---

## PHASE 3: TURN 1 - DELETE REQUEST (5 minutes)

### Step 3.1: Clear Terminal Logs

In Terminal 1 (backend logs), scroll to the bottom and note the timestamp.

### Step 3.2: Run Test - Ask Bot to Delete

In the chat UI, type:
```
"delete test delete me"
```

### Step 3.3: IMMEDIATELY Capture Logs

In Terminal 1, scroll back and **copy all logs since you started**.

Looking specifically for these patterns:

```
[PENDING ACTION DETECTION] Response:
[PENDING ACTION DETECTION] Delete phrase detected:
[PENDING ACTION] Detected deletion confirmation request:
[PENDING ACTION STORAGE] ✅ Adding pending_action to metadata:
[METADATA] Final metadata to store:
[MESSAGE STORAGE] Stored assistant message
```

### Step 3.4: Create DEBUG FILE 1

Save these logs to a file: `debug_turn1.log`

### Step 3.5: Verify Bot Response

In the chat, you should see:
```
Bot: "I found the task 'test delete me' (ID: 5). Are you sure you want to delete it?"
```

**CRITICAL CHECK**: Does the bot response include:
- ✅ `"(ID: 5)"` format?
- ✅ `"Are you sure"` phrase?

**If NO**: Bot is not asking for confirmation properly
- **SKIP TO: Issue #1 (Agent Instructions)**

**If YES**: Continue to Step 3.6

### Step 3.6: Analyze Turn 1 Logs

In your `debug_turn1.log`, search for each of these and note what you find:

```
SEARCH 1: "[PENDING ACTION DETECTION] Delete phrase detected:"
EXPECTED: "Delete phrase detected: True"
ACTUAL: ___________________
FOUND: ✅ or ❌

SEARCH 2: "[PENDING ACTION] Detected deletion confirmation request:"
EXPECTED: "Detected deletion confirmation request: task_id=5, title='test delete me'"
ACTUAL: ___________________
FOUND: ✅ or ❌

SEARCH 3: "[PENDING ACTION STORAGE] ✅ Adding pending_action to metadata:"
EXPECTED: "Adding pending_action to metadata: {type: delete_task, task_id: 5, ...}"
ACTUAL: ___________________
FOUND: ✅ or ❌

SEARCH 4: "[METADATA] Final metadata to store:"
EXPECTED: "pending_action=True"
ACTUAL: ___________________
FOUND: ✅ or ❌
```

### Step 3.7: Determine Turn 1 Status

```
If all 4 searches found ✅:
  → TURN 1 WORKING - Go to PHASE 4

If any search shows ❌ or NOT FOUND:
  → TURN 1 BROKEN - Go to TROUBLESHOOTING
```

---

## PHASE 4: TURN 2 - CONFIRMATION (5 minutes)

### Step 4.1: Clear Terminal Again

Scroll to bottom of Terminal 1.

### Step 4.2: Send Confirmation Message

In the chat, type:
```
"yes"
```

### Step 4.3: Capture Turn 2 Logs

In Terminal 1, scroll back and copy all logs since you sent "yes".

Looking for:
```
[PENDING ACTION STATE MACHINE] Entering pending action handler
[PENDING ACTION STATE MACHINE] Retrieved last assistant message
[PENDING ACTION STATE MACHINE] Metadata keys found:
[PENDING ACTION STATE MACHINE] Found pending_action in metadata
[PENDING ACTION STATE MACHINE] Confirmation check:
[PENDING ACTION STATE MACHINE] ✅ USER CONFIRMED
[PENDING ACTION] Delete tool result:
[PENDING ACTION] Successfully deleted task_id=
```

### Step 4.4: Create DEBUG FILE 2

Save to: `debug_turn2.log`

### Step 4.5: Analyze Turn 2 Logs

Search for each pattern:

```
SEARCH 1: "[PENDING ACTION STATE MACHINE] Entering pending action handler"
EXPECTED: YES
ACTUAL: ___________________
FOUND: ✅ or ❌

SEARCH 2: "[PENDING ACTION STATE MACHINE] Retrieved last assistant message"
EXPECTED: "Retrieved last assistant message id=42"
ACTUAL: ___________________
FOUND: ✅ or ❌

SEARCH 3: "[PENDING ACTION STATE MACHINE] Metadata keys found:"
EXPECTED: "['tool_calls', 'action', 'pending_action']"
ACTUAL: ___________________
FOUND: ✅ or ❌

SEARCH 4: "[PENDING ACTION STATE MACHINE] Found pending_action in metadata"
EXPECTED: YES
ACTUAL: ___________________
FOUND: ✅ or ❌

SEARCH 5: "Confirmation check: is_confirmation="
EXPECTED: "is_confirmation=True"
ACTUAL: ___________________
FOUND: ✅ or ❌

SEARCH 6: "[PENDING ACTION] Successfully deleted task_id="
EXPECTED: YES (with task ID)
ACTUAL: ___________________
FOUND: ✅ or ❌
```

### Step 4.6: Check Chat Result

Look at the bot's response:
```
EXPECTED: "✓ Deleted task 'test delete me' (ID: 5)"
ACTUAL: ___________________

Did task get deleted? ✅ or ❌
```

### Step 4.7: Determine Overall Status

```
If all searches ✅ AND task deleted:
  → ✅ ISSUE FIXED! Done!

If any search ❌:
  → ❌ ISSUE NOT FIXED - Continue to TROUBLESHOOTING
```

---

## TROUBLESHOOTING: Find The Issue

### ISSUE #1: Bot Not Asking for Confirmation

**Symptom**:
```
User: "delete test"
Bot: "I couldn't find that task..." (or similar error)
```

**OR Bot says**: `"Which task would you like to delete?"` (multiple matches)

**Root Cause**: Agent not finding task or finding multiple

**Solution**:
1. Verify task actually exists in database
2. Use exact task name from list
3. Try: `"delete test delete me"` (exact match)
4. Check agent instructions in `chat_service.py` line ~76

**Fix Code**:
```python
# In AGENT_INSTRUCTIONS, ensure delete section says:
# "If exactly ONE task matches:"
#   * Show the task name and ID: "I found the task '[task title]' (ID: {id}). Are you sure you want to delete it?"
```

---

### ISSUE #2: Delete Phrase Not Detected

**Symptom**:
```
[PENDING ACTION DETECTION] Delete phrase detected: False
```

**Root Cause**: Bot response doesn't match our regex patterns

**Check**:
```
What was the exact bot response?
Expected patterns: "Are you sure", "confirm", "delete"
```

**Solution**:

Find the exact phrase the bot used and add it to patterns:

In `chat_service.py` line ~793:
```python
delete_confirmation_patterns = [
    r"Are you sure you want to delete",
    r"Do you want to delete",
    # ADD YOUR BOT'S EXACT PHRASE HERE:
    r"<exact phrase from bot response>",
]
```

**Example**: If bot says `"Should I delete 'task'?"` add:
```python
r"Should I delete",
```

---

### ISSUE #3: Task ID Not Extracted

**Symptom**:
```
[PENDING ACTION DETECTION] Delete phrase detected: True
BUT NO "Detected deletion confirmation request" log
```

**Root Cause**: Task ID format doesn't match our regex

**Check**:
```
What was the exact ID format in bot response?
Expected: "(ID: 5)" but got: "_______"
```

**Solution**:

In `chat_service.py` line ~800, update ID patterns:
```python
id_patterns = [
    r'\(ID:\s*(\d+)\)',  # (ID: 5)
    r'ID[:\s=]+(\d+)',    # ID: 5 or ID=5
    # ADD YOUR FORMAT HERE:
    r'<exact ID format>',
]
```

**Example**: If bot says `"task #5"` add:
```python
r'#(\d+)',
```

---

### ISSUE #4: Pending Action Not Stored

**Symptom**:
```
[PENDING ACTION] Detected deletion confirmation request: task_id=5
BUT NO "[PENDING ACTION STORAGE] ✅ Adding pending_action"
```

**Root Cause**: Error during pending_action creation

**Check logs for**:
```
[PENDING ACTION] Failed to parse task_id
ValueError or TypeError messages
```

**Solution**:

Look in `chat_service.py` around line 824-835 for error handling.

If you see errors like:
```
ValueError: invalid literal for int()
```

The task_id extraction regex is wrong. Go back to ISSUE #3.

---

### ISSUE #5: Pending Action in Metadata But Not Retrieved

**Symptom**:
```
Turn 1: [PENDING ACTION STORAGE] ✅ Adding pending_action to metadata
Turn 2: [PENDING ACTION STATE MACHINE] No last assistant message found
```

**Root Cause**: Message not being saved to database OR wrong conversation_id

**Check**:
1. Is `session.commit()` being called in `store_message()`?
2. Is conversation_id the SAME in both turns?

**Solution**:

In `chat_service.py` line ~495:
```python
session.add(message)
session.commit()  # ← MUST BE HERE
session.refresh(message)
```

Verify it's there.

---

### ISSUE #6: Metadata Not Being Retrieved

**Symptom**:
```
Turn 2: Retrieved last assistant message id=42
BUT: No metadata on last assistant message
```

**Root Cause**: `message.get_metadata()` returning None

**Check**: Is metadata_json empty in database?

```sql
SELECT metadata_json FROM message WHERE id=42;
-- Should show: {"tool_calls": [...], "pending_action": {...}}
```

**Solution**:

In `chat_service.py` line ~491:
```python
if metadata:
    message.set_metadata(metadata)  # ← Must be called
```

Check it's being called before `session.add(message)`.

---

### ISSUE #7: Metadata Has No pending_action

**Symptom**:
```
Turn 2: Metadata keys found: ['tool_calls', 'action']
(pending_action is MISSING)
```

**Root Cause**: `pending_action` variable is None or not added to metadata

**Solution**:

In `chat_service.py` line ~949:
```python
if pending_action:
    metadata["pending_action"] = pending_action
```

Check:
1. Is `pending_action` variable being set in Turn 1?
2. Is this code executing?

Add logging if needed:
```python
logger.info(f"DEBUG: pending_action = {pending_action}")
logger.info(f"DEBUG: metadata before = {metadata}")
if pending_action:
    metadata["pending_action"] = pending_action
logger.info(f"DEBUG: metadata after = {metadata}")
```

---

### ISSUE #8: Pending Action Found But "yes" Not Recognized

**Symptom**:
```
Turn 2: Found pending_action in metadata
BUT: Confirmation check: is_confirmation=False
```

**Root Cause**: "yes" not in AFFIRMATIVE_PATTERNS

**Solution**:

In `chat_service.py` line ~39:
```python
AFFIRMATIVE_PATTERNS = {
    "yes",  # ← Must have "yes"
    "confirm", "ok", "sure", "yeah", "yep",
    "proceed", "delete it", "go ahead", "do it"
}
```

If "yes" is missing, add it.

Also check the `is_confirmation()` function (line ~50):
```python
def is_confirmation(message: str) -> bool:
    normalized = message.lower().strip().strip('.,!?')
    # "yes" → "yes" (should match)
    return normalized in AFFIRMATIVE_PATTERNS
```

Test it manually:
```python
message = "yes"
normalized = message.lower().strip().strip('.,!?')
print(normalized in AFFIRMATIVE_PATTERNS)  # Should be True
```

---

### ISSUE #9: Delete Tool Not Found

**Symptom**:
```
Found pending_action and confirmed
BUT: delete_task tool not found
```

**Root Cause**: Task tools not created or delete_task missing

**Solution**:

In `chat_service.py` line ~294:
```python
tools_list = create_task_tools(user_id=user_id, session=session)
delete_tool = next((t for t in tools_list if t.__name__ == "delete_task"), None)

if not delete_tool:
    logger.error("delete_task tool not found!")
```

Check:
1. Is `create_task_tools()` returning tools?
2. Does it include `delete_task`?

In `task_tools.py` line ~269, verify delete_task exists:
```python
@function_tool
def delete_task(task_id: int) -> str:
    """..."""
```

---

### ISSUE #10: Delete Tool Executed But Returned Error

**Symptom**:
```
Delete tool result: "Task 5 not found..."
Successfully deleted: False
```

**Root Cause**: Task doesn't exist OR user doesn't own task

**Solution**:

In `task_tools.py` line ~281:
```python
task = session.exec(
    select(Task).where(Task.id == task_id, Task.user_id == user_id)
).first()

if not task:
    return f"Task {task_id} not found..."
```

Check:
1. Does task exist in database?
2. Does it belong to the logged-in user?

Run SQL:
```sql
SELECT id, title, user_id FROM task WHERE id=5;
-- Verify user_id matches your user
```

---

## STEP 4: Report Findings

Create a summary file: `DEBUG_FINDINGS.txt`

```
=== DEBUG FINDINGS ===

TURN 1 Status: ✅ WORKING / ❌ BROKEN
Issue (if broken): Issue #___

TURN 2 Status: ✅ WORKING / ❌ BROKEN
Issue (if broken): Issue #___

Logs File 1: debug_turn1.log
Logs File 2: debug_turn2.log

Specific Error Messages:
[Copy error messages from logs]

Bot Response in Turn 1:
[Copy exact bot response]

Bot Response in Turn 2:
[Copy exact bot response]

User Input in Turn 2:
[What user typed]

Did Task Delete?: ✅ YES / ❌ NO
```

---

## STEP 5: Apply Fix

Once you identify the issue number, apply the corresponding fix from the TROUBLESHOOTING section above.

### After Each Fix:

1. Save the file
2. Restart backend
3. Re-run the test (Steps 1-4)
4. Verify the issue is resolved
5. If new issue appears, continue troubleshooting

---

## QUICK REFERENCE: Expected Logs

### If Everything Works, You Should See:

**Turn 1:**
```
[PENDING ACTION DETECTION] Response: 'I found the task "test" (ID: 5). Are you sure...'
[PENDING ACTION DETECTION] Delete phrase detected: True
[PENDING ACTION] Detected deletion confirmation request: task_id=5, title='test'
[PENDING ACTION STORAGE] ✅ Adding pending_action to metadata
[MESSAGE STORAGE] Stored assistant message message_id=42
```

**Turn 2:**
```
[PENDING ACTION STATE MACHINE] Entering pending action handler
[PENDING ACTION STATE MACHINE] Retrieved last assistant message id=42
[PENDING ACTION STATE MACHINE] Metadata keys found: ['tool_calls', 'action', 'pending_action']
[PENDING ACTION STATE MACHINE] ✅ Found pending_action in metadata
[PENDING ACTION STATE MACHINE] Confirmation check: is_confirmation=True, is_cancellation=False
[PENDING ACTION STATE MACHINE] ✅ USER CONFIRMED delete_task for task_id=5
[PENDING ACTION] Delete tool result: "Deleted task 'test' (ID: 5)"
[PENDING ACTION] Successfully deleted task_id=5
```

**Chat Result:**
```
Bot: "✓ Deleted task 'test' (ID: 5)"
Task List: Task removed ✅
```

---

## FILES TO HAVE READY

Before starting:
- [ ] `debug_turn1.log` - Backend logs for Turn 1
- [ ] `debug_turn2.log` - Backend logs for Turn 2
- [ ] `DEBUG_FINDINGS.txt` - Your analysis
- [ ] Text editor with this guide open

---

**Total Time**: 15-20 minutes
**Next**: Report findings and apply fix
