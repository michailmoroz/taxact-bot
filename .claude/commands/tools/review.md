---
description: Code review based on execution report
argument-hint: <execution-report-path>
---

# Review: Code Review

Review the changes from execution report: **$ARGUMENTS**

## Purpose

Use this command after `/execute` and before `/commit` to:

- Catch issues before they reach the repository
- Verify code quality, security, and performance
- Ensure best practices are followed
- Validate test coverage

---

## Process Overview

```
1. READ REPORT   → Understand what was changed
2. LOAD FILES    → Read all created/modified files
3. REVIEW        → Check all aspects systematically
4. FINDINGS      → Categorize and prioritize issues
5. FIX OPTIONS   → Offer to fix issues
6. REPORT        → Generate review report
```

---

## Phase 1: Read Execution Report

Read the execution report from: `$ARGUMENTS`

Extract:
- **Files Created**: New files to review
- **Files Modified**: Changed files to review
- **Tests Added**: Test files to verify
- **Feature Context**: What was implemented

---

## Phase 2: Load Files

Read ALL files mentioned in the execution report:

1. New files (full review)
2. Modified files (focus on changes)
3. Test files (verify coverage)
4. Related files (check for missed impacts)

---

## Phase 3: Systematic Review

Review each file against ALL aspects:

### 3.1 Security

| Check | What to Look For |
|-------|------------------|
| **Injection** | SQL, Command, XSS, Template injection |
| **Authentication** | Proper auth checks, session handling |
| **Authorization** | Access control, privilege escalation |
| **Secrets** | Hardcoded keys, tokens, passwords |
| **Input Validation** | Sanitization, type checking, bounds |
| **Output Encoding** | HTML escaping, JSON encoding |
| **Dependencies** | Known vulnerabilities, outdated packages |

### 3.2 Code Quality

| Check | What to Look For |
|-------|------------------|
| **DRY** | Duplicated code, copy-paste patterns |
| **SOLID** | Single responsibility, proper abstractions |
| **Complexity** | Deep nesting, long functions, god objects |
| **Readability** | Clear names, logical structure, comments where needed |
| **Error Handling** | Try-catch, error propagation, user feedback |
| **Edge Cases** | Null checks, empty arrays, boundary conditions |

### 3.3 Performance

| Check | What to Look For |
|-------|------------------|
| **Database** | N+1 queries, missing indexes, large fetches |
| **Memory** | Leaks, large allocations, retained references |
| **Rendering** | Unnecessary re-renders, missing memoization |
| **Network** | Excessive requests, missing caching, large payloads |
| **Algorithms** | O(n²) loops, inefficient searches |

### 3.4 Tests

| Check | What to Look For |
|-------|------------------|
| **Coverage** | All new functions tested? |
| **Edge Cases** | Boundary conditions, error paths |
| **Assertions** | Meaningful checks, not just "runs without error" |
| **Isolation** | Tests independent, no shared state |
| **Naming** | Clear test names describing behavior |

### 3.5 Consistency

| Check | What to Look For |
|-------|------------------|
| **Naming** | Matches codebase conventions |
| **Patterns** | Follows established architecture |
| **Style** | Beyond linting: idioms, structure |
| **Documentation** | Matches project standards |

---

## Phase 4: Categorize Findings

### Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| **Critical** | Security vulnerability, data loss risk | Must fix before commit |
| **High** | Bug, incorrect behavior | Should fix before commit |
| **Medium** | Code smell, maintainability issue | Recommend fixing |
| **Low** | Style, minor improvement | Optional |
| **Info** | Observation, suggestion | FYI only |

### Finding Format

```markdown
### [SEVERITY] Finding Title

**Location**: `file:line`

**Issue**: What's wrong

**Risk**: Why this matters

**Suggested Fix**:
```code
// proposed change
```

**Fix command**: "Fix this" / "Skip"
```

---

## Phase 5: Offer Fixes

For each finding (Critical, High, Medium):

```markdown
## Findings Summary

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 1 | Critical | SQL Injection | api/users.ts:45 |
| 2 | High | Missing null check | lib/parser.ts:23 |
| 3 | Medium | Duplicated validation | forms/login.ts:67 |

---

### Finding 1: SQL Injection

[Details...]

**Should I fix this?** (yes/no/skip all)
```

### Fix Workflow

| User Response | Action |
|---------------|--------|
| "yes" or "y" | Apply the suggested fix |
| "no" or "n" | Skip this finding |
| "skip all" | Skip remaining fixes, just report |
| "fix all" | Apply all suggested fixes |
| Custom text | User provides alternative fix |

---

## Phase 6: Generate Review Report

Create `.agents/review-reports/{feature}-{date}.md`:

```markdown
# Review Report: {Feature Name}

## Meta

- **Date**: {YYYY-MM-DD}
- **Execution Report**: {path}
- **Status**: Passed | Passed with Fixes | Needs Attention
- **Reviewer**: Claude

## Summary

| Severity | Count | Fixed |
|----------|-------|-------|
| Critical | 0 | 0 |
| High | 2 | 2 |
| Medium | 3 | 1 |
| Low | 5 | 0 |
| Info | 2 | - |

**Verdict**: {Ready to commit / Needs more work}

## Files Reviewed

| File | Lines | Issues |
|------|-------|--------|
| `path/to/file.ts` | 45-120 | 2 |

## Findings

### Critical

(none)

### High

#### 1. Missing null check

- **Location**: `lib/parser.ts:23`
- **Issue**: `data.user` accessed without null check
- **Status**: Fixed

### Medium

#### 2. Duplicated validation logic

- **Location**: `forms/login.ts:67`, `forms/register.ts:34`
- **Issue**: Same email validation in two places
- **Status**: Noted (not fixed)
- **Recommendation**: Extract to shared utility

### Low

[...]

### Info

[...]

## Security Checklist

- [x] No hardcoded secrets
- [x] Input validation present
- [x] SQL queries parameterized
- [ ] Rate limiting (not applicable)

## Test Coverage

- [x] Happy path tested
- [x] Error cases tested
- [ ] Edge case: empty input (missing)

## Recommendations

1. {Follow-up action}
2. {Improvement suggestion}

## Verdict

**Ready to commit**: Yes / No

**Blocking issues**: {list or "none"}
```

---

## Phase 7: Summary to User

```markdown
## Review Complete

**Status**: Passed with Fixes

### Findings
- Critical: 0
- High: 2 (fixed)
- Medium: 3 (1 fixed, 2 noted)
- Low: 5 (skipped)

### Fixes Applied
1. Added null check in parser.ts:23
2. Fixed SQL injection in users.ts:45

### Still Open
- Duplicated validation (medium) - consider refactoring later

### Verdict
Ready to commit. Run `/commit {execution-report-path}`
```

---

## Guidelines

### Review Mindset

1. **Be thorough but practical** - Don't nitpick, focus on real issues
2. **Explain the "why"** - Help understand, not just criticize
3. **Suggest, don't demand** - User decides what to fix
4. **Context matters** - Consider the feature's purpose

### What NOT to Flag

- Style issues already caught by linter
- Personal preferences without objective benefit
- "I would do it differently" without clear improvement
- Theoretical issues that can't happen in context

### Severity Guidelines

| Severity | Criteria |
|----------|----------|
| Critical | Could cause security breach, data loss, or crash |
| High | Incorrect behavior, bug that users will encounter |
| Medium | Works but hard to maintain, potential future bug |
| Low | Could be better, minor improvement |
| Info | FYI, learning opportunity, nice-to-know |

---

## Example Usage

```
/review .agents/execution-reports/add-user-auth-2025-02-11.md
```

---

## Example Output

```
## Review Complete: .agents/review-reports/add-user-auth-2025-02-11.md

### Summary
- 0 Critical, 2 High, 4 Medium, 3 Low

### Immediate Attention
1. [High] SQL injection in userQuery - FIXED
2. [High] Missing CSRF token - FIXED

### Recommendations
- Extract email validation to shared utility
- Add rate limiting to login endpoint (future task)

### Verdict
✓ Ready to commit

Next: `/commit .agents/execution-reports/add-user-auth-2025-02-11.md`
```
