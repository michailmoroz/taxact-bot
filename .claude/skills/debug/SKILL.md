---
name: debug
description: Structured debugging with root-cause analysis
argument-hint: "<bug description>"
disable-model-invocation: true
user-invocable: true
---

# Debug: Root-Cause Analysis

Systematically debug and find the root cause of: **$ARGUMENTS**

## Purpose

Use this command when something doesn't work as expected:

- Application crashes or errors
- Unexpected behavior
- Failed tests
- Performance issues

This command finds the root cause and proposes a fix. You decide whether to implement it.

---

## Process Overview

```
1. UNDERSTAND  → Clarify the bug
2. REPRODUCE   → Confirm the bug exists
3. HYPOTHESIZE → Form theories about the cause
4. INVESTIGATE → Test hypotheses systematically
5. ROOT-CAUSE  → Identify the actual cause
6. FIX         → Propose solution for user approval
7. REPORT      → Document findings
```

---

## Phase 1: Understand the Bug

### 1.1 Gather Information

Ask clarifying questions if needed:

- What is the expected behavior?
- What is the actual behavior?
- When did it start happening?
- Is it reproducible? (always / sometimes / rarely)
- Any recent changes that might be related?

### 1.2 Classify Bug Type

| Type | Indicators | Primary Tools |
|------|------------|---------------|
| **UI/Frontend** | Visual issues, click not working, layout broken | Playwright, DevTools, DOM |
| **API/Backend** | 500 errors, wrong response, timeout | Logs, curl, request/response |
| **Logic** | Wrong calculation, unexpected result | Unit tests, debugger, traces |
| **Data** | Missing data, wrong state, corruption | DB queries, state inspection |
| **Performance** | Slow, hanging, memory issues | Profiler, traces, metrics |

---

## Phase 2: Reproduce the Bug

**Goal:** Confirm the bug exists and create a reliable reproduction.

### Reproduction Methods by Bug Type

| Bug Type | Method |
|----------|--------|
| **UI/Frontend** | Playwright: Navigate, screenshot, inspect DOM |
| **API/Backend** | curl/fetch request, check logs, inspect response |
| **Logic** | Write a failing unit test that demonstrates the bug |
| **Data** | Query database, inspect application state |
| **Performance** | Run profiler, measure timing, check memory |

### Reproduction Checklist

- [ ] Bug confirmed (reproduced at least once)
- [ ] Steps to reproduce documented
- [ ] Environment noted (browser, OS, Node version, etc.)
- [ ] Error messages captured

**If bug cannot be reproduced:**
1. Ask user for more details
2. Check if environment-specific
3. Look for race conditions / timing issues

---

## Phase 3: Form Hypotheses

Based on the bug type and symptoms, form 2-4 hypotheses:

```markdown
### Hypothesis 1: [Title]
- **Theory**: What might be causing this
- **Evidence for**: Why this could be the cause
- **Evidence against**: Why this might not be the cause
- **Test**: How to verify this hypothesis
```

### Hypothesis Prioritization

Test hypotheses in this order:
1. **Most likely** based on evidence
2. **Easiest to verify** (quick wins)
3. **Most impactful** if true

---

## Phase 4: Investigate Systematically

For each hypothesis:

### 4.1 Gather Evidence

- Read relevant code files
- Check git history (`git log`, `git blame`)
- Search for similar patterns
- Inspect logs and error messages

### 4.2 Test the Hypothesis

| Hypothesis Status | Action |
|-------------------|--------|
| **Confirmed** | → Proceed to Phase 5 |
| **Disproven** | → Document why, test next hypothesis |
| **Inconclusive** | → Gather more evidence or refine hypothesis |

### 4.3 Document Each Test

```markdown
#### Testing Hypothesis 1
- **Action taken**: What I did to test
- **Result**: What I observed
- **Conclusion**: Confirmed / Disproven / Inconclusive
```

---

## Phase 5: Identify Root Cause

Once a hypothesis is confirmed:

### 5.1 Verify Root Cause

- [ ] Explains ALL observed symptoms
- [ ] Can predict the bug's behavior
- [ ] Changing this would fix the bug

### 5.2 Document Root Cause

```markdown
## Root Cause

**Location**: `file:line`

**Cause**: [Clear explanation of what's wrong]

**Why it happens**: [The underlying reason]

**Impact**: [What this bug affects]
```

---

## Phase 6: Propose Fix

**Do NOT implement automatically. Propose and wait for user approval.**

### 6.1 Design the Fix

Consider:
- Minimal change that fixes the bug
- No side effects on working functionality
- Follows existing code patterns
- Includes test to prevent regression

### 6.2 Present Fix Options

```markdown
## Proposed Fix

### Option A: [Name] (Recommended)

**Change**: What to modify

**File**: `path/to/file.ts:line`

**Before**:
```code
// current code
```

**After**:
```code
// fixed code
```

**Pros**: Why this is good
**Cons**: Any downsides

### Option B: [Name] (Alternative)

[Same format]

---

**Which fix should I implement?**
- A: [Description]
- B: [Description]
- C: Something else (please describe)
- D: Don't fix, just document
```

### 6.3 Wait for User Decision

- User chooses option → Implement the fix
- User rejects all → Document bug only
- User suggests alternative → Discuss and implement

---

## Phase 7: Generate Debug Report

Create `.agents/debug-reports/{bug-name}-{date}.md`:

```markdown
# Debug Report: {Bug Title}

## Meta

- **Date**: {YYYY-MM-DD}
- **Status**: Fixed | Documented | Unresolved
- **Severity**: Critical | High | Medium | Low

## Bug Summary

**Reported**: {Original bug description}

**Expected**: {What should happen}

**Actual**: {What actually happens}

## Reproduction

**Steps**:
1. {Step 1}
2. {Step 2}
3. {Bug occurs}

**Environment**: {Browser, OS, versions}

## Investigation

### Hypotheses Tested

| # | Hypothesis | Result |
|---|------------|--------|
| 1 | {Theory} | Confirmed / Disproven |
| 2 | {Theory} | Confirmed / Disproven |

### Evidence Gathered

| Source | Finding |
|--------|---------|
| `file:line` | {What was found} |
| Logs | {Relevant log entries} |

## Root Cause

**Location**: `{file:line}`

**Cause**: {Clear explanation}

**Why**: {Underlying reason}

## Fix Applied

**Option chosen**: {A/B/C or None}

**Changes made**:
| File | Change |
|------|--------|
| `path/to/file` | {Description} |

**Regression test**: `{test file or command}`

## Lessons Learned

- {What could prevent similar bugs}
- {Process improvements}
```

---

## Guidelines

### Debugging Principles

1. **Reproduce first** - Never guess without confirmation
2. **One change at a time** - Isolate variables
3. **Trust the evidence** - Don't assume, verify
4. **Minimal fix** - Change only what's necessary
5. **Prevent regression** - Add test for the bug

### Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Fixing symptoms, not cause | Ask "why?" 5 times |
| Too many changes at once | Revert, change one thing |
| Assuming without testing | Write a test that fails |
| Ignoring edge cases | Check boundary conditions |

### When to Escalate

Stop and ask user if:
- Bug cannot be reproduced after multiple attempts
- Root cause is in third-party code
- Fix requires architectural changes
- Multiple valid fixes with significant tradeoffs

---

## Example Usage

```
/debug Login button doesn't respond after failed attempt

/debug API returns 500 error on user update

/debug Tests pass locally but fail in CI

/debug App freezes when loading large dataset
```

---

## Example Summary Output

```
## Debug Complete: .agents/debug-reports/login-button-frozen-2025-02-11.md

### Root Cause
Event listener removed after failed login attempt due to
error handler calling `removeEventListener` instead of retry logic.

Location: `src/auth/login.ts:142`

### Proposed Fix
Option A (Recommended): Remove erroneous removeEventListener call
Option B: Add re-attachment logic in error recovery

Which fix should I implement? (A/B/other)
```
