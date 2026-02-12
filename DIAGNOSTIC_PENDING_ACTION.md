# Diagnostic Guide: Why Pending Action Handler Not Working

**Date**: 2026-02-11
**Issue**: Pending action not being detected/stored/retrieved
**Status**: Diagnosing with enhanced logging

---

## The Problem Symptom

```
Turn 1:
User: "delete my pasta task"
Bot:  "I found the task "make creamy pasta" (ID: 13). Are you sure you want to delete it?"

Turn 2:
User: "yes"
Bot:  "It looks like you responded with "yes." Could you please clarify..."
  ❌ Task NOT deleted
  ❌ Bot forgot the pending action
  ❌ Agent processed "yes" as a regular message instead of confirmation
```

---

## Diagnostic Flow

### Step 1: Check If Pending Action Detected in Turn 1

**Look for these logs** (in Turn 1 when bot asks for confirmation):
```
[PENDING ACTION DETECTION] Response: 'I found the task "make creamy pasta" (ID: 13). Are you sure...'
[PENDING ACTION DETECTION] Delete phrase detected: True
[PENDING ACTION] Detected deletion confirmation request: task_id=13, title='make creamy pasta'
[PENDING ACTION STORAGE] ✅ Adding pending_action to metadata: {...}
```

**If you see:**
- ✅ `Delete phrase detected: True` → Detection working
- ✅ `Detected deletion confirmation request` → Pattern matched
- ✅ `Adding pending_action to metadata` → Stored in metadata

**If you see:**
- ❌ `Delete phrase detected: False` → **Issue #1: Pattern not matching**
- ❌ No "Detected deletion confirmation request" → **Issue #2: ID/title not extracted**
- ❌ `No pending_action to store` → **Issue #3: Pending action not created**

---

### Step 2: Check If Message Stored with Pending Action

**Look for this log** (after Turn 1):
```
[MESSAGE STORAGE] Stored assistant message message_id=123, conversation_id=456
[METADATA] Final metadata to store: ['tool_calls', 'action', 'pending_action'] - pending_action=True
```

**If you see:**
- ✅ `pending_action=True` in metadata dict → Message stored correctly

**If you see:**
- ❌ `pending_action=False` in metadata → **Issue #4: Pending action lost before storage**
- ❌ No "MESSAGE STORAGE" log → **Database error**

---

### Step 3: Check If Pending Action Retrieved in Turn 2

**Look for these logs** (in Turn 2 when user says "yes"):
```
[PENDING ACTION STATE MACHINE] Entering pending action handler
[PENDING ACTION STATE MACHINE] Retrieved last assistant message id=123, content_preview='I found the task...'
[PENDING ACTION STATE MACHINE] Metadata keys found: ['tool_calls', 'action', 'pending_action']
[PENDING ACTION STATE MACHINE] ✅ Found pending_action in metadata!
[PENDING ACTION STATE MACHINE] Confirmation check: is_confirmation=True, is_cancellation=False
[PENDING ACTION STATE MACHINE] ✅ USER CONFIRMED delete_task
```

**If you see:**
- ✅ All logs with ✅ checkmarks → **Pending action handler working!**

**If you see:**
- ❌ `No last assistant message found` → **Issue #5: Database not returning message**
- ❌ `No metadata on last assistant message` → **Issue #6: Message has no metadata**
- ❌ `No pending_action in metadata` → **Issue #7: Metadata lost between turns**
- ❌ `Confirmation check: is_confirmation=False` → **Issue #8: "yes" not recognized**

---

## Diagnostic Issues & Solutions

### Issue #1: Delete Phrase Not Detected

**Symptom**: `Delete phrase detected: False`

**Root Cause**: Bot response doesn't match any pattern

**Diagnostic**:
1. Check the exact bot response in the log
2. See if it contains: "Are you sure", "confirm", "delete"
3. Check regex pattern matching

**Solution**:
Add bot's exact phrase to detection patterns in code (line ~795):
```python
delete_confirmation_patterns = [
    r"Are you sure you want to delete",
    r"Do you want to delete",
    # ADD YOUR PATTERN HERE
    r"<exact phrase from bot response>",
]
```

---

### Issue #2: Task ID Not Extracted

**Symptom**: Delete phrase detected but no "Detected deletion confirmation" log

**Root Cause**: Task ID not found in response (wrong format)

**Diagnostic**:
1. Check bot response for ID format
2. Look for patterns like: `(ID: 13)`, `ID=13`, `#13`
3. Test regex pattern

**Solution**:
Add the ID format to extraction patterns (line ~800):
```python
id_patterns = [
    r'\(ID:\s*(\d+)\)',  # (ID: 13)
    r'ID[:\s=]+(\d+)',    # ID: 13 or ID=13
    # ADD YOUR PATTERN HERE
    r'<exact ID format from bot>',
]
```

---

### Issue #3: Pending Action Not Created

**Symptom**: ID extracted but "Adding pending_action to metadata" log missing

**Root Cause**: Error during pending_action dict creation

**Solution**:
Check exception logs around line ~824-835. Any `ValueError` or `TypeError`?

---

### Issue #4: Pending Action Lost Before Storage

**Symptom**: Detected but not in metadata when stored

**Root Cause**: Pending action variable overwritten or scoped incorrectly

**Diagnostic**:
Check if there's any code between detection (line 780) and storage (line 950) that modifies `pending_action`

---

### Issue #5: Database Not Returning Message

**Symptom**: `No last assistant message found`

**Root Cause**: Message not committed to database OR querying wrong table

**Solution**:
1. Check if store_message is calling session.commit()
2. Check conversation_id is the same between turns
3. Check database has messages

---

### Issue #6: Message Has No Metadata

**Symptom**: `No metadata on last assistant message`

**Root Cause**: Message stored without calling set_metadata()

**Solution**:
Check store_message function (line ~460):
```python
if metadata:
    message.set_metadata(metadata)  # Must be called
```

---

### Issue #7: Metadata Lost Between Turns

**Symptom**: Message retrieved but pending_action not in metadata dict

**Root Cause**: JSON serialization/deserialization issue

**Diagnostic**:
Check `message.get_metadata()` is properly deserializing JSON:
```python
def get_metadata(self) -> Optional[dict]:
    if self.metadata_json:
        try:
            return json.loads(self.metadata_json)
        except json.JSONDecodeError:
            return None  # ← Returns None on JSON error!
    return None
```

**Solution**:
If JSON deserialization failing, check metadata_json content directly in database

---

### Issue #8: "yes" Not Recognized as Confirmation

**Symptom**: `is_confirmation=False` for user input "yes"

**Root Cause**: Confirmation patterns don't match

**Diagnostic**:
Check `is_confirmation()` function (line ~50):
```python
def is_confirmation(message: str) -> bool:
    normalized = message.lower().strip().strip('.,!?')
    # normalized is now "yes"
    return normalized in AFFIRMATIVE_PATTERNS  # Check if "yes" in set
```

**Solution**:
Ensure "yes" is in AFFIRMATIVE_PATTERNS (line ~40):
```python
AFFIRMATIVE_PATTERNS = {
    "yes",  # ← Must be here
    "confirm", "ok", "sure", "yeah", "yep", ...
}
```

---

## Complete Log Sequence (Expected)

### Turn 1: Delete Request
```
[CONVERSATION LIFECYCLE] Processing message for user_id=user123
[MESSAGE STORAGE] Stored user message "delete my pasta task"
[PENDING ACTION STATE MACHINE] Entering pending action handler
[PENDING ACTION STATE MACHINE] No last assistant message found  ← First turn, no previous message
[EXECUTION FLOW] No pending action found, proceeding to agent execution
[AGENT EXECUTION] Running agent with tools
[TOOL CALL TRACKING] AI tool call: tool=list_tasks
[PENDING ACTION DETECTION] Response: 'I found the task "make creamy pasta" (ID: 13). Are you sure...'
[PENDING ACTION DETECTION] Delete phrase detected: True
[PENDING ACTION] Detected deletion confirmation request: task_id=13, title='make creamy pasta'
[ACTION DETECTION] Final action determination: action=conversation (list_tasks doesn't modify)
[PENDING ACTION STORAGE] ✅ Adding pending_action to metadata
[METADATA] Final metadata to store: ['tool_calls', 'action', 'pending_action'] - pending_action=True
[MESSAGE STORAGE] Stored assistant message message_id=42, action=conversation, pending_action=present
[CONVERSATION LIFECYCLE] Completed message processing
```

### Turn 2: User Confirmation
```
[CONVERSATION LIFECYCLE] Processing message for user_id=user123
[MESSAGE STORAGE] Stored user message "yes"
[PENDING ACTION STATE MACHINE] Entering pending action handler
[PENDING ACTION STATE MACHINE] Retrieved last assistant message id=42, content_preview='I found the task...'
[PENDING ACTION STATE MACHINE] Metadata keys found: ['tool_calls', 'action', 'pending_action']
[PENDING ACTION STATE MACHINE] ✅ Found pending_action in metadata!
[PENDING ACTION STATE MACHINE] Checking user message for confirmation/cancellation. Message: 'yes'
[PENDING ACTION STATE MACHINE] Confirmation check: is_confirmation=True, is_cancellation=False
[PENDING ACTION STATE MACHINE] ✅ USER CONFIRMED delete_task for task_id=13
[PENDING ACTION] Delete tool result: "Deleted task 'make creamy pasta' (ID: 13)"
[PENDING ACTION] Successfully deleted task_id=13
[MESSAGE STORAGE] Stored assistant message with action=task_deleted
[CONVERSATION LIFECYCLE] Returning ChatResponse with action=task_deleted
```

---

## How to Run Diagnostic

### 1. Enable All Logging
```bash
# In backend logs, set level to DEBUG or INFO
LOGLEVEL=INFO python -m uvicorn ...
```

### 2. Run Test Sequence
1. Open chat
2. Say: "delete any task name"
3. Copy all backend logs
4. Say: "yes"
5. Copy all backend logs

### 3. Analyze Logs
Compare your logs to the "Expected" sequence above. Find the first divergence point.

### 4. Report Issue
Share:
- Exact bot response
- All logs mentioning `[PENDING ACTION`
- All logs mentioning `[METADATA]`
- All logs mentioning `[CONVERSATION LIFECYCLE]`

---

## Quick Check List

Run through this to find the issue:

```
Turn 1 Logs:
□ Do you see "[PENDING ACTION DETECTION] Response:" log?
  YES → Go to next
  NO → **Issue #1: Detection not running**

□ Do you see "Delete phrase detected: True"?
  YES → Go to next
  NO → **Issue #1: Pattern not matching bot response**

□ Do you see "Detected deletion confirmation request:"?
  YES → Go to next
  NO → **Issue #2: Task ID not extracted**

□ Do you see "Adding pending_action to metadata"?
  YES → Go to next
  NO → **Issue #3: Pending action not created**

□ Do you see "Stored assistant message" with "pending_action=True"?
  YES → Turn 1 complete, check Turn 2
  NO → **Issue #4: Metadata lost**

Turn 2 Logs:
□ Do you see "Entering pending action handler"?
  YES → Go to next
  NO → **Issue #5: Handler not called**

□ Do you see "Retrieved last assistant message"?
  YES → Go to next
  NO → **Issue #5: Message not in database**

□ Do you see "Found pending_action in metadata"?
  YES → Go to next
  NO → **Issue #7: Metadata lost between turns**

□ Do you see "is_confirmation=True"?
  YES → Go to next
  NO → **Issue #8: "yes" not recognized**

□ Do you see "USER CONFIRMED" and "Successfully deleted"?
  YES → ✅ WORKING!
  NO → Check delete_task tool execution
```

---

## Files to Check

1. **Log Detection**: `backend/src/services/chat_service.py` lines 787-837
2. **Storage**: `backend/src/services/chat_service.py` lines 948-960
3. **Retrieval**: `backend/src/services/chat_service.py` lines 269-305
4. **Confirmation**: `backend/src/services/chat_service.py` lines 50-59
5. **Metadata Model**: `backend/src/models/chat.py` lines 45-67

---

## Next Steps

1. Deploy updated code with enhanced logging
2. Run test sequence: "delete [task]" → "yes"
3. Capture full backend logs
4. Identify which diagnostic issue applies
5. Fix specific issue based on diagnostics above

---

**Purpose**: This guide helps isolate exactly where the pending action flow is breaking.
