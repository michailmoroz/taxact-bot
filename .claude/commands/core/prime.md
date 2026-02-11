---
description: Load project context and provide summary
argument-hint: [focus: full|status|structure]
---

# Prime: Project Context

Load and summarize project context for the current session.

## Instructions

### 1. Read Core Documents

Read in this order, skip if file doesn't exist:

1. `CLAUDE.md` → Project identity, conventions, structure
2. `README.md` → Overview, installation, tech stack
3. `.agents/PRD.md` → Current status, roadmap, next tasks
4. `.agents/references/architecture.md` → Detailed architecture (if exists)

### 2. Analyze Project

- **Structure**: Scan top 2 directory levels (ignore node_modules, .venv, __pycache__, .git)
- **Tech Stack**: Detect from config files:
  - `package.json` → Node.js/JavaScript
  - `requirements.txt` / `pyproject.toml` → Python
  - `go.mod` → Go
  - `Cargo.toml` → Rust
  - `*.csproj` → C#/.NET
- **Git Status**: Current branch, uncommitted changes count

### 3. Output Summary

Provide a concise, scannable summary:

```
## Project: [Name from CLAUDE.md or README.md]

[1-2 sentence description]

## Status [from PRD.md if exists]

- **Phase**: [current phase]
- **In Progress**: [current task]
- **Next**: [next tasks]

## Tech Stack

- **Language**: [detected]
- **Framework**: [detected]
- **Key Dependencies**: [top 3-5]

## Structure

[Key directories and their purpose, max 10 lines]

## Git

- **Branch**: [current]
- **Changes**: [X uncommitted files]

## Ready

Context loaded. What would you like to work on?
```

## Focus Modes

Based on `$ARGUMENTS`:

| Argument | Output |
|----------|--------|
| (empty) or `full` | Complete summary (all sections) |
| `status` | Only Status section from PRD.md |
| `structure` | Only project structure analysis |
| `tech` | Only tech stack detection |

## Guidelines

- Keep output **concise and scannable**
- Use **bullet points and tables**
- Don't repeat what's already in CLAUDE.md verbatim
- Focus on **actionable context** for the session
- If PRD.md has open tasks, highlight the next one
