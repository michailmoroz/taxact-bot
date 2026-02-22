---
name: prd
description: Create or update the project PRD (Product Requirements Document)
argument-hint: "[create|update|status]"
disable-model-invocation: true
user-invocable: true
---

# PRD: Project Requirements Document

Create or update the project PRD in `.agents/PRD.md`

## Modes

| Argument | Action |
|----------|--------|
| (empty) or `create` | Create new PRD (asks if one exists) |
| `update` | Update existing PRD |
| `status` | Show current PRD status |

---

## Phase 1: Detect Current State

### 1.1 Check for Existing PRD

```
Check if .agents/PRD.md exists
```

| State | Mode = create | Mode = update |
|-------|---------------|---------------|
| PRD exists | Ask: "PRD exists. Update instead?" | Proceed to update flow |
| PRD missing | Proceed to create flow | Ask: "No PRD found. Create one?" |

### 1.2 Read Context (if updating)

If PRD exists, read and understand:
- Current project goal
- Existing phases and tasks
- Current status

---

## Phase 2: Interview (REQUIRED)

**Always ask questions to understand the user's needs.**

### 2.1 For CREATE Mode

Ask using AskUserQuestion tool:

**Question Set 1: Project Basics**
- What is this project about? (if not clear from CLAUDE.md/README.md)
- What is the main goal or outcome?
- Who is the target user/audience?

**Question Set 2: Scope**
- Is this a new project or extending an existing one?
- What are the key features or milestones?
- Are there known constraints (time, tech, dependencies)?

**Question Set 3: Structure**
- How should work be organized? (Phases, Epics, simple task list)
- Are there dependencies between tasks?
- What's the definition of "done" for this project?

### 2.2 For UPDATE Mode

Ask using AskUserQuestion tool:

**Question Set 1: What to Update**
- What should be updated? (Status, new tasks, completed items, scope change)
- Which phase or section needs changes?

**Question Set 2: Reason**
- Why is this update needed? (Progress, new requirements, pivot, bug discovered)
- Should existing tasks be modified or just status updated?

**Question Set 3: Validation**
- Show current state and proposed changes
- Confirm before applying

---

## Phase 3: Gather Information

### 3.1 Read Project Context

If not already in context, read:
1. `CLAUDE.md` - Project conventions
2. `README.md` - Project overview
3. Existing `.agents/PRD.md` (if updating)

### 3.2 Analyze Codebase (for existing projects)

- Scan project structure
- Identify existing features
- Note tech stack and patterns

---

## Phase 4: Generate PRD

### 4.1 PRD Template

```markdown
# PRD: {Project Name}

## Project Goal

{2-3 sentences: What is being built and why}

### Target Users

{Who will use this}

### Success Criteria

- [ ] {Measurable outcome 1}
- [ ] {Measurable outcome 2}

---

## Current Status

**Phase**: {current phase number/name}
**Progress**: {X of Y tasks completed}
**Last Updated**: {date}

---

## Roadmap

### Phase 1: {Phase Name}

| Task | Description | Status |
|------|-------------|--------|
| 1.1 | {Task description} | {Ausstehend/In Arbeit/Erledigt} |
| 1.2 | {Task description} | {Status} |

### Phase 2: {Phase Name}

| Task | Description | Status |
|------|-------------|--------|
| 2.1 | {Task description} | {Status} |

{Continue for all phases}

---

## Constraints & Dependencies

### Technical Constraints

- {Constraint 1}
- {Constraint 2}

### External Dependencies

- {Dependency 1}
- {Dependency 2}

---

## Open Questions

- [ ] {Question that needs to be resolved}
- [ ] {Decision that needs to be made}

---

## Changelog

| Date | Change |
|------|--------|
| {date} | PRD created |
```

### 4.2 Customization Based on Interview

Adjust template based on answers:

| Project Type | Adjustments |
|--------------|-------------|
| Small/Simple | Minimal phases, simple task list |
| Feature | Focus on acceptance criteria |
| Research | Include findings section |
| Refactoring | Include before/after metrics |
| Migration | Include rollback strategy |

---

## Phase 5: Update Flow (if mode = update)

### 5.1 Types of Updates

| Update Type | Action |
|-------------|--------|
| **Status** | Mark tasks as In Arbeit/Erledigt |
| **New Tasks** | Add tasks to existing phase |
| **New Phase** | Add new phase to roadmap |
| **Scope Change** | Modify goals, add/remove features |
| **Completed** | Mark phase or project as done |

### 5.2 Update Process

1. Show current state of section to update
2. Propose changes based on user input
3. Ask for confirmation
4. Apply changes
5. Update "Last Updated" date
6. Add entry to Changelog

---

## Phase 6: Validate & Save

### 6.1 Pre-Save Checklist

- [ ] Project goal is clear
- [ ] At least one phase defined
- [ ] Tasks are actionable (not vague)
- [ ] Status values are consistent

### 6.2 Save

- Create `.agents/` directory if needed
- Write to `.agents/PRD.md`
- Confirm save to user

---

## Phase 7: Summary

### For CREATE

```markdown
## PRD Created: .agents/PRD.md

### Overview
- **Project**: {name}
- **Phases**: {count}
- **Total Tasks**: {count}

### Next Steps
1. Review the PRD
2. Start with Phase 1
3. Use `/planning {first task}` to begin

Ready to start? Use `/prime` to load context.
```

### For UPDATE

```markdown
## PRD Updated: .agents/PRD.md

### Changes Made
- {Change 1}
- {Change 2}

### Current Status
- **Phase**: {current}
- **Progress**: {X/Y tasks}

### Next Task
{Next pending task from roadmap}
```

---

## Guidelines

### Interview Best Practices

1. **Don't assume** - Ask if unclear
2. **Summarize understanding** - "So you want to build X that does Y?"
3. **Offer options** - "Would you prefer A or B?"
4. **Confirm before writing** - Show structure before saving

### PRD Quality

- **Actionable tasks** - Each task should be completable
- **Clear status** - Use consistent status values
- **Reasonable scope** - Not too granular, not too vague
- **Living document** - Expect updates as project evolves

### Status Values

Use consistent German status values:
- `Ausstehend` - Not started
- `In Arbeit` - In progress
- `Review` - Waiting for review
- `Erledigt` - Completed

---

## Example Usage

```
/prd
→ "No PRD found. Let me ask some questions..."
→ Interview
→ Creates .agents/PRD.md

/prd update
→ "What would you like to update?"
→ User: "Mark Phase 1 as complete"
→ Updates status, adds changelog entry

/prd status
→ Shows current phase, progress, next tasks
```

---

## Error Handling

| Situation | Response |
|-----------|----------|
| User gives vague answers | Ask follow-up: "Can you be more specific about X?" |
| Conflicting requirements | Point out conflict, ask for clarification |
| Scope too large | Suggest breaking into phases |
| No clear goal | Ask: "What problem are you trying to solve?" |
