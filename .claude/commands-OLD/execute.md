---
description: Execute a development plan with full Archon task management integration
argument-hint: [plan-file-path]
---

# Execute Development Plan

Execute the plan from: **$ARGUMENTS**

## Critical Requirements

1. Generate execution report BEFORE committing
2. Document all divergences from plan with justifications

## Execution Workflow

### Step 1: Read and Understand
- Read the ENTIRE plan file
- Understand all tasks and their dependencies
- Note the validation commands to run
- Review the resting strategy

### Step 1.5: Plan Audit (Quality Gate)

**Before proceeding, audit the plan for completeness.**

Run a quick completeness check based on feature type:

**1. Determine feature characteristics:**

- Is it a deployment/infrastructure/some other feature?
- What complexity? (Low/Medium/High)

**2. Check required sections exist:**

| Feature Type | Required Sections |
|--------------|-------------------|
| ALL | User Story, STEP-BY-STEP TASKS, VALIDATION COMMANDS |
| Deployment | DEPLOYMENT CONTEXT (ports, server paths) |
| Medium+ Complexity | COMPLEXITY ANALYSIS, TESTING STRATEGY |

**3. Decision matrix:**

| Missing Sections | Action |
|------------------|--------|
| None | ✅ Proceed to Step 2 |
| Optional only | ✅ Proceed (note in report) |
| Required sections | ⚠️ Ask user: proceed anyway or update plan first? |
| Backend capability gap | ⚠️ Ask user: descope feature or implement backend first? |

**4. If blocking issues found:**

Ask user:
> "Plan audit found issues:
> - [Issue 1]
> - [Issue 2]
>
> Options:
> 1. Proceed anyway (document gaps in execution report)
> 2. Update plan first
> 3. Cancel execution"

### Step 2: Codebase Analysis

**Before implementation:**
1. Read ALL referenced files from plan
2. Verify patterns still apply
3. Check dependencies exist: `grep "express" package.json`
4. If dependencies missing: Install FIRST, then proceed

**If version mismatch:**
1. Check library's documentation for API differences
2. Update code patterns to match installed version (see CLAUDE.md)
3. Document divergence in execution report
   
### Step 3: Execute Tasks in Order

For EACH task in "Step by Step Tasks":

**a. Navigate to the task**
- Identify the file and action required
- Read existing related files if modifying
  
**b. Implement the task**
- Follow the detailed specifications exactly
- Maintain consistency with existing code patterns
- Include proper type hints and documentation
- Add structured logging where appropriate

**c. Verify as you go**
- After each file change, check syntax
- Ensure imports are correct
- Verify types are properly defined

### Step 4 Implement Testing Strategy

After completing implementation tasks:

- Create all test files specified in the plan
- Implement all test cases mentioned
- Follow the testing approach outlined
- Ensure tests cover edge cases

**4.1 Code Style Check**

Verify code follows CLAUDE.md conventions:

- File naming: `kebab-case.js`
- Functions: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- ES Modules: `import/export` (not `require`)
- Structured logging: JSON format

### Step 5: Validation

**Development server**

npm run dev

**Should start without errors**

**Health check**

curl http://localhost:3000/health

**Should return JSON with correct metadata**

**Code Quality Check:**
- [ ] No hardcoded values (use env vars)
- [ ] Structured JSON logging implemented
- [ ] Error handlers configured
- [ ] Health check returns correct metadata

Execute ALL validation commands from the plan in order:

```bash
# Run each command exactly as specified in plan
```

If any command fails:
- Fix the issue
- Re-run the command
- Continue only when it passes

**5.1 Final Verification**

Before completing:

- ✅ All tasks from plan completed
- ✅ All tests created and passing
- ✅ All validation commands pass
- ✅ Code follows project conventions
- ✅ Documentation added/updated as needed

### Step 6: Generate Execution Report

Create `.agents/execution-reports/{feature-name}.md`:

```markdown
# Execution Report: {Feature Name}

## Meta Information
- **Plan file:** {path}
- **Date:** {date}
- **Archon tracking:** enabled/local fallback

## Implementation Summary

### Files Created
- `path/to/file.ts` - Description

### Files Modified
- `path/to/file.ts` - What changed

### Tests Added
- `path/to/test.ts` - What is tested

## Divergences from Plan

| Planned | Actual | Reason | Justified |
|---------|--------|--------|-----------|
| X | Y | Why | yes/no |

## Validation Results
- [x] `npm run dev` - started successfully
- [x] `/health` endpoint - returns correct JSON
- [x] Docker build - succeeded
- [x] Docker run - health check passed
- [x] docker-compose - local environment works

## Issues Encountered
- {issue} - {resolution}

## Skipped Items (Automation Blockers)
| Task | Command | Reason | Next Step |
|------|---------|--------|-----------|
| Task N | `example command` | Example reason | Example next step |

## Task Summary
- Created: N / Completed: N / In Review: N / Deferred: N
```

### Step 7: Summary

Report to user:
- Tasks created/completed
- Test coverage achieved
- Key features implemented
- Path to execution report

## Notes

- If you encounter issues not addressed in the plan, document them
- If you need to deviate from the plan, explain why
- If tests fail, fix implementation until they pass
- Don't skip validation steps