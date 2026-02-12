# Debug Checklist - Quick Reference

Use this while following the step-by-step guide.

---

## PHASE 1: SETUP ✓

- [ ] Backend logs visible in terminal
- [ ] Logging level set to INFO
- [ ] Backend restarted
- [ ] Text editor open for notes

---

## PHASE 2: PREPARATION ✓

- [ ] Task created with known ID
- [ ] Chat conversation ready
- [ ] Clipboard ready to capture logs

---

## PHASE 3: TURN 1 - DELETE REQUEST

### Run Test
```bash
User sends: "delete [task name]"
```

### Capture Logs
**In terminal, look for:**

```
□ [PENDING ACTION DETECTION] Response: 'I found the task...'
   Expected: YES
   Actual: _______________

□ [PENDING ACTION DETECTION] Delete phrase detected:
   Expected: True
   Actual: _______________

□ [PENDING ACTION] Detected deletion confirmation request:
   Expected: YES (with task_id and title)
   Actual: _______________

□ [PENDING ACTION STORAGE] ✅ Adding pending_action to metadata:
   Expected: YES
   Actual: _______________

□ [METADATA] Final metadata to store:
   Expected: pending_action=True
   Actual: _______________
```

### Bot Response Check
```
□ Bot says: "Are you sure you want to delete it?"
   Expected: YES (with task ID in parentheses)
   Actual: _______________
   Format: (ID: X)?  YES / NO
```

### Turn 1 Status
```
□ All checkboxes above = ✅  → TURN 1 WORKING - Go to PHASE 4
□ Any checkbox = ❌          → TURN 1 BROKEN - Note which ❌ and go to TROUBLESHOOTING
□ Not found                  → TURN 1 BROKEN - Same as above

Issues found: _______________
```

---

## PHASE 4: TURN 2 - CONFIRMATION

### Run Test
```bash
User sends: "yes"
```

### Capture Logs
**In terminal, look for:**

```
□ [PENDING ACTION STATE MACHINE] Entering pending action handler
   Expected: YES
   Actual: _______________
   Issue: ISSUE #5

□ [PENDING ACTION STATE MACHINE] Retrieved last assistant message
   Expected: YES (with message id)
   Actual: _______________
   Issue: ISSUE #5

□ [PENDING ACTION STATE MACHINE] Metadata keys found:
   Expected: YES (includes 'pending_action')
   Actual: _______________
   Issue: ISSUE #6 or #7

□ [PENDING ACTION STATE MACHINE] Found pending_action in metadata
   Expected: YES
   Actual: _______________
   Issue: ISSUE #7

□ [PENDING ACTION STATE MACHINE] Confirmation check:
   Expected: is_confirmation=True
   Actual: _______________
   Issue: ISSUE #8

□ [PENDING ACTION STATE MACHINE] ✅ USER CONFIRMED
   Expected: YES
   Actual: _______________
   Issue: (Previous issue)

□ [PENDING ACTION] Delete tool result:
   Expected: "Deleted task..." (not error message)
   Actual: _______________
   Issue: ISSUE #9 or #10

□ [PENDING ACTION] Successfully deleted task_id=
   Expected: YES
   Actual: _______________
```

### Bot Response Check
```
□ Bot says: "✓ Deleted task..."
   Expected: YES
   Actual: _______________

□ Task was deleted from database?
   Expected: YES
   Actual: _______________
```

### Turn 2 Status
```
□ All checkboxes above = ✅  → ✅ ISSUE FIXED! Done!
□ Any checkbox = ❌          → ❌ ISSUE NOT FIXED

Which issue number(s): _______________
```

---

## ISSUE QUICK FIX MAP

```
If Turn 1 BROKEN:
└─ [PENDING ACTION DETECTION] Delete phrase detected: False
   → ISSUE #1 or #2
   → Fix: Update detection patterns in chat_service.py line ~793

└─ Detected deletion confirmation request: NOT FOUND
   → ISSUE #2 or #3
   → Fix: Update ID extraction patterns in chat_service.py line ~800

└─ Adding pending_action to metadata: NOT FOUND
   → ISSUE #4
   → Fix: Check error logs around line ~824-835

└─ metadata to store: pending_action=False
   → ISSUE #7
   → Fix: Verify pending_action is added to dict at line ~949

If Turn 2 BROKEN:
└─ Entering pending action handler: NOT FOUND
   → ISSUE #5
   → Fix: Check if handle_pending_action() is called at line ~577

└─ Retrieved last assistant message: NOT FOUND
   → ISSUE #5
   → Fix: Check conversation_id or database

└─ Metadata keys found: NO pending_action
   → ISSUE #6 or #7
   → Fix: Check session.commit() at line ~495

└─ Found pending_action in metadata: NOT FOUND
   → ISSUE #7
   → Fix: Check metadata storage (line ~949)

└─ is_confirmation=False
   → ISSUE #8
   → Fix: Add "yes" to AFFIRMATIVE_PATTERNS at line ~39

└─ Delete tool result: ERROR message
   → ISSUE #9 or #10
   → Fix: Check delete_task tool in task_tools.py
```

---

## COPY-PASTE COMMANDS

### Terminal 1: Start Backend with Logs
```bash
cd /mnt/d/Hackathon_Projects/hackathon_project2/The-Evolution-of-Todo-Application/backend
python -m uvicorn src.main:app --reload --log-level info
```

### Terminal 2: Find Specific Logs
```bash
# Copy logs and search for patterns
grep "\[PENDING ACTION" debug_turn1.log
grep "\[PENDING ACTION" debug_turn2.log

# Count occurrences
grep -c "\[PENDING ACTION DETECTION\]" debug_turn1.log
grep -c "\[PENDING ACTION STATE MACHINE\]" debug_turn2.log
```

### Database Check
```bash
# If using SQLite
sqlite3 /path/to/database.db "SELECT id, role, content, metadata_json FROM message WHERE role='assistant' ORDER BY created_at DESC LIMIT 2;"

# If using PostgreSQL
psql -U username -d dbname -c "SELECT id, role, content, metadata_json FROM message WHERE role='assistant' ORDER BY created_at DESC LIMIT 2;"
```

---

## FILES TO CREATE

Create these files to save your debug session:

### File 1: `debug_turn1.log`
```
=== TURN 1: DELETE REQUEST ===
[Paste all backend logs from Turn 1]

BOT RESPONSE:
[Paste exact bot message]

ANALYSIS:
Delete phrase detected: ___
Task ID extracted: ___
Pending action stored: ___
```

### File 2: `debug_turn2.log`
```
=== TURN 2: CONFIRMATION ===
[Paste all backend logs from Turn 2]

BOT RESPONSE:
[Paste exact bot message]

ANALYSIS:
Handler called: ___
Pending action found: ___
Confirmation detected: ___
Task deleted: ___
```

### File 3: `DEBUG_FINDINGS.txt`
```
=== DEBUG FINDINGS ===

TURN 1: ✅ WORKING / ❌ BROKEN
Turn 1 Issue: _______________

TURN 2: ✅ WORKING / ❌ BROKEN
Turn 2 Issue: _______________

ROOT CAUSE (Issue #): _______________

BOT RESPONSE (Turn 1):
[Exact bot message]

BOT RESPONSE (Turn 2):
[Exact bot message]

USER INPUT (Turn 2):
[What user typed]

TASK DELETED: ✅ YES / ❌ NO

NEXT ACTION: _______________
```

---

## COMMON FINDINGS

### Finding A: "Delete phrase detected: False"
**Means**: Bot response doesn't match regex pattern
**Action**:
1. Check bot response format
2. Add pattern to `delete_confirmation_patterns`
3. Re-test

### Finding B: "Metadata keys found: ['tool_calls', 'action']" (no pending_action)
**Means**: Pending action wasn't stored in Turn 1
**Action**:
1. Review Turn 1 logs more carefully
2. Look for detection issue
3. Or metadata wasn't added to dict

### Finding C: Handler called but no "Found pending_action"
**Means**: Database query returned message but metadata is empty
**Action**:
1. Check if session.commit() is called
2. Check if set_metadata() is called
3. Verify in database directly

### Finding D: "is_confirmation=False"
**Means**: "yes" not in AFFIRMATIVE_PATTERNS
**Action**:
1. Add "yes" to set at line ~39
2. Re-test

---

## SUCCESS INDICATORS

When working correctly, you should see:

**Turn 1 Logs Include:**
```
✅ [PENDING ACTION DETECTION] Delete phrase detected: True
✅ [PENDING ACTION] Detected deletion confirmation request: task_id=X
✅ [PENDING ACTION STORAGE] ✅ Adding pending_action to metadata
✅ [METADATA] Final metadata to store: pending_action=True
```

**Turn 2 Logs Include:**
```
✅ [PENDING ACTION STATE MACHINE] Entering pending action handler
✅ [PENDING ACTION STATE MACHINE] ✅ Found pending_action in metadata
✅ [PENDING ACTION STATE MACHINE] ✅ USER CONFIRMED delete_task
✅ [PENDING ACTION] Successfully deleted task_id=X
```

**Chat Shows:**
```
✅ Bot: "✓ Deleted task '[name]' (ID: X)"
✅ Task removed from list
```

---

## TIME TRACKING

- [ ] Setup: 5 min
- [ ] Turn 1: 5 min
- [ ] Turn 2: 5 min
- [ ] Analysis: 5 min
- **Total**: 20 minutes

---

## FINAL CHECKLIST

Before you start:
- [ ] Backend restarted
- [ ] Logs visible
- [ ] Text editor ready
- [ ] This guide open
- [ ] Know the task ID to delete

During test:
- [ ] Capturing all logs
- [ ] Noting findings
- [ ] Testing both turns
- [ ] Checking chat UI

After test:
- [ ] Logs saved to files
- [ ] Findings documented
- [ ] Issue identified
- [ ] Ready to fix or report

---

**Ready to debug?** Start from PHASE 1 in `STEP_BY_STEP_DEBUG.md`
