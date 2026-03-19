---
name: execute
description: Execute an implementation plan with testing and validation
argument-hint: "<plan-file-path>"
disable-model-invocation: false
user-invocable: true
---

# Execute: Implement Plan

Execute the plan from: **$ARGUMENTS**

## Process Overview

```
1. READ PLAN → Understand tasks and dependencies
2. AUDIT PLAN → Check completeness (Quality Gate)
3. PREPARE → Install dependencies, read referenced files
4. EXECUTE → Implement each task with tests
5. VALIDATE → Run all tests and checks
6. REPORT → Generate execution report
```

---

## Phase 1: Read and Understand

1. Read the ENTIRE plan file
2. Understand all tasks and their dependencies
3. Note the validation commands
4. Review testing requirements
5. Check rollback strategy

---

## Phase 2: Plan Audit (Quality Gate)

**Before proceeding, verify plan completeness:**

### Required Sections

| Section | Required |
|---------|----------|
| User Story | Yes |
| Acceptance Criteria | Yes |
| Tasks | Yes |
| Testing Requirements | Yes |

### Decision Matrix

| Status | Action |
|--------|--------|
| All sections present | Proceed to Phase 3 |
| Optional sections missing | Proceed, note in report |
| Required sections missing | Ask user: proceed or update plan? |

**If blocking issues found, ask user:**
```
Plan audit found issues:
- [Issue 1]
- [Issue 2]

Options:
1. Proceed anyway (document in report)
2. Update plan first
3. Cancel execution
```

---

## Phase 3: Prepare

### 3.1 Read Referenced Files

- Read ALL files mentioned in plan's "Relevant Files" section
- Verify patterns still apply
- Check for recent changes that might affect implementation

### 3.2 Install Dependencies

If plan lists new packages:

```
Check CLAUDE.md for package manager commands, then:
- Install listed dependencies
- Verify installation successful
- Document any version conflicts
```

### 3.3 Verify Prerequisites

- All dependencies installed
- Referenced files exist
- No blocking issues

---

## Phase 4: Execute Tasks

**For EACH task in the plan:**

### 4.1 Implement

1. Read the task specification
2. Check dependencies (other tasks that must complete first)
3. Read pattern reference files if specified
4. Implement the changes
5. Follow code style from CLAUDE.md

### 4.2 Write Tests (Parallel with Implementation)

For each task, write tests that verify:
- The functionality works as expected
- Edge cases are handled
- No regressions introduced

**Test approach:**
- Write test alongside implementation (not after all tasks)
- Each task should have its own test(s)
- Follow existing test patterns in codebase

### 4.3 Validate Task

After each task, run validation:

```
1. Syntax check (file saves without errors)
2. Imports correct
3. Types valid (if applicable)
4. Task-specific validation from plan
```

**Only proceed to next task when current task passes validation.**

---

## Phase 5: Testing Strategy

Execute tests in order (commands from CLAUDE.md):

### Level 1: Static Analysis

```
Run lint check (eslint, ruff, etc.)
Run type check (tsc, mypy, etc.)
```

### Level 2: Unit Tests

```
Run unit tests for new/modified code
Verify all tests pass
```

### Level 3: Integration Tests

```
Run integration tests
Verify API/module interactions work
```

### Level 4: E2E Tests (if in Testing Requirements)

```
Run Playwright or equivalent
Verify user flows work end-to-end
```

### Test Failure Handling

If tests fail:
1. Analyze failure reason
2. Fix the implementation (NOT the test, unless test is wrong)
3. Re-run tests
4. Continue only when tests pass

**Important:** Do NOT modify working code outside the scope of this plan.

---

## Phase 6: Bug Handling

During implementation:

| Bug Type | Action |
|----------|--------|
| Caused by THIS implementation | Fix immediately |
| Pre-existing bug discovered | Document in `.agents/bugs/{date}-{name}.md`, do NOT fix |
| Outside scope of plan | Document, do NOT fix |

---

## Phase 7: Final Validation

Before generating report:

- [ ] All tasks from plan completed
- [ ] All tests written and passing
- [ ] Lint check passes
- [ ] Type check passes (if applicable)
- [ ] No regressions in existing functionality
- [ ] Acceptance criteria met
- [ ] Manual verification steps completed (if any)

---

## Phase 8: Generate Execution Report

Create `.agents/execution-reports/{feature-name}-{date}.md`:

```markdown
# Execution Report: {Feature Name}

## Meta
- **Plan file:** {path}
- **Date:** {date}
- **Status:** Completed / Partial / Failed

## Summary
- **Tasks completed:** X / Y
- **Tests written:** N
- **Tests passing:** N / N

## Files Changed

### Created
| File | Purpose |
|------|---------|
| `path/to/file` | Description |

### Modified
| File | Changes |
|------|---------|
| `path/to/file` | What changed |

## Tests Added
| Test File | Coverage |
|-----------|----------|
| `path/to/test` | What is tested |

## Validation Results
- [ ] Lint: passed/failed
- [ ] Type check: passed/failed
- [ ] Unit tests: X/X passed
- [ ] Integration tests: X/X passed
- [ ] E2E tests: X/X passed (if applicable)

## Divergences from Plan
| Planned | Actual | Reason |
|---------|--------|--------|
| X | Y | Why the change was necessary |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| Description | How it was resolved |

## Bugs Discovered (not fixed)
| Bug | Location | Documented in |
|-----|----------|---------------|
| Description | file:line | `.agents/bugs/...` |

## Manual Verification
- [ ] {Check from plan}
- [ ] {Check from plan}

## Next Steps
- {Any follow-up tasks}
- {Recommendations}
```

---

## Phase 9: Summary to User

Report to user:
1. Tasks completed (X/Y)
2. Tests written and passing
3. Any divergences from plan
4. Any issues encountered
5. Path to execution report
6. Recommendation for next steps (commit, review, etc.)

---

## Guidelines

### Code Style
- Follow conventions from CLAUDE.md
- Run lint tools to verify compliance
- Match existing patterns in codebase

### Testing
- Each new function should have tests
- Follow existing test patterns
- Cover happy path + edge cases

### Documentation
- Update comments if behavior changes
- Update README if user-facing changes
- Do NOT add unnecessary documentation

### Git
- Do NOT commit automatically
- User decides when to commit (use `/commit`)
