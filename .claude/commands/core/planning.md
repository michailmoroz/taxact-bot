---
description: Create a comprehensive implementation plan for a feature
argument-hint: <feature-description>
---

# Planning: Create Implementation Plan

Create a detailed, executable implementation plan for: **$ARGUMENTS**

## Process

### Phase 1: Clarify Requirements

**Before planning, ask clarifying questions using AskUserQuestion tool:**

- What is the exact scope of this feature?
- Are there specific technical constraints or preferences?
- What are the must-have vs. nice-to-have requirements?
- Are there existing patterns in the codebase to follow?
- What are potential edge cases to consider?

**Continue only after user has answered the questions.**

### Phase 2: Research Codebase

Analyze the codebase to understand:

1. **Relevant Files**: Find similar features or related code
2. **Patterns**: How are similar things implemented?
3. **Conventions**: Check CLAUDE.md for project rules (already in context)
4. **Current Status**: Reference PRD.md for project state (already in context)

**Do NOT re-read CLAUDE.md or PRD.md if already in context.**

### Phase 3: Design

Make architectural decisions:

1. **New Files**: What needs to be created?
2. **Modified Files**: What existing files need changes?
3. **Dependencies**: New packages required?
4. **Breaking Changes**: Will this break existing functionality?

### Phase 4: Create Plan

Write the plan to `.agents/plans/{kebab-case-name}.md`

**Follow the Output Format below exactly.**

---

## Output Format

```markdown
# Plan: {Feature Name}

## User Story

Als [Rolle] möchte ich [Funktion], damit [Nutzen].

## Acceptance Criteria

- [ ] {Criterion 1}
- [ ] {Criterion 2}
- [ ] {Criterion 3}

## Context

{2-3 sentences: What is being built and why}

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `path/to/file` | {why relevant} | {specific lines} |

### Patterns to Follow
{Description of patterns found in codebase with file:line references}

## Dependencies

- **New Packages**: {list or "none"}
- **Affected Modules**: {list}
- **Breaking Changes**: {yes/no, if yes: details}

## Tasks

Execute tasks in order. Each task is atomic and independently verifiable.

### Task 1: {ACTION} `{file}`

- **Action**: CREATE | UPDATE | ADD | REMOVE | REFACTOR
- **Implement**: {Specific description of what to do}
- **Pattern**: Reference `{file:line}` for similar implementation
- **Depends on**: {Task numbers or "none"}
- **Validate**: `{command to verify this task}`

### Task 2: {ACTION} `{file}`
...

{Continue for all tasks}

## Testing Requirements

Tests to be written during /execute:

- [ ] {What to test 1}
- [ ] {What to test 2}
- [ ] Edge case: {description}

**Test Levels**: Unit | Integration | E2E (as appropriate)

## Bug Handling

During implementation:
- Bugs caused by THESE changes → Fix immediately
- Pre-existing bugs discovered → Document in `.agents/bugs/`, do NOT fix
- NEVER modify working code outside the scope of this plan

## Rollback Strategy

If implementation fails:
1. `git stash` or `git checkout .` to revert changes
2. {Additional rollback steps if needed}

## Manual Verification

After implementation, manually verify:
- [ ] {UI check or functional test 1}
- [ ] {UI check or functional test 2}

## Notes

{Any additional context, warnings, or considerations}
```

---

## Guidelines

### Plan Quality

- **Max 800 lines** (absolute limit: 1000)
- **Atomic tasks**: Each task should be completable in one step
- **Specific references**: Use `file:line` not vague descriptions
- **No redundancy**: Don't repeat information across sections
- **Executable**: Another developer could follow this plan without asking questions

### Task Format

Use action keywords:
- **CREATE**: New file
- **UPDATE**: Modify existing file
- **ADD**: Add new functionality to existing code
- **REMOVE**: Delete code or files
- **REFACTOR**: Restructure without changing behavior

### Validation Commands

Each task should have a validation command:
- `npm run lint`
- `npm run typecheck`
- `npm run test -- {specific test}`
- `grep -r "pattern" src/` (to verify changes exist)

---

## After Plan Creation

1. **Save** the plan to `.agents/plans/{kebab-case-name}.md`
2. **Summarize** the plan for the user:
   - Number of tasks
   - Estimated complexity (Low/Medium/High)
   - Key risks or considerations
3. **Ask** if user wants to proceed with `/execute` or make changes

---

## Example Summary Output

```
## Plan Created: .agents/plans/add-user-authentication.md

### Summary
- **Tasks**: 8
- **New Files**: 3
- **Modified Files**: 5
- **New Packages**: jsonwebtoken, bcrypt
- **Breaking Changes**: No
- **Complexity**: Medium

### Key Considerations
- Requires database migration
- Session handling needs careful testing

Ready to execute with `/execute .agents/plans/add-user-authentication.md`
```
