---
name: create-claude
description: Create a comprehensive CLAUDE.md with interview and auto-detection
argument-hint: "[update]"
disable-model-invocation: true
user-invocable: true
---

# Create-Claude: Generate CLAUDE.md

Create or update a comprehensive CLAUDE.md for this project.

**Replaces `/init`** with more structure, interview phase, and focus on actionable commands.

## Modes

| Argument | Action |
|----------|--------|
| (empty) | Create new CLAUDE.md |
| `update` | Update existing CLAUDE.md |

---

## Phase 1: Detect Current State

### 1.1 Check for Existing CLAUDE.md

```
Check if CLAUDE.md exists in project root
```

| State | Mode = create | Mode = update |
|-------|---------------|---------------|
| CLAUDE.md exists | Ask: "CLAUDE.md exists. Update instead?" | Proceed to update flow |
| CLAUDE.md missing | Proceed to create flow | Ask: "No CLAUDE.md found. Create one?" |

### 1.2 Auto-Detect Project Info

Scan project for:

| File | Extracts |
|------|----------|
| `package.json` | Name, scripts (lint, test, build), dependencies |
| `requirements.txt` / `pyproject.toml` | Python project, dependencies |
| `go.mod` | Go project, module name |
| `Cargo.toml` | Rust project, crate name |
| `*.csproj` | .NET project |
| `.eslintrc*` | Lint configuration |
| `jest.config.*` / `vitest.config.*` | Test framework |
| `tsconfig.json` | TypeScript configuration |
| `.prettierrc*` | Code formatting |
| `Dockerfile` | Containerization |
| `.github/workflows/*` | CI/CD setup |

---

## Phase 2: Interview (REQUIRED)

**Always ask questions to fill gaps not covered by auto-detection.**

### 2.1 Project Basics

Ask using AskUserQuestion tool:

- What is this project? (if not clear from package.json/README)
- What is the main purpose in 1-2 sentences?

### 2.2 Commands & Scripts

For each detected script, confirm or ask:

**Lint:**
- Detected: `npm run lint` - Correct?
- Or: What command runs linting?

**Tests:**
- Detected: `npm test` - Correct?
- Or: What command runs tests?
- Are there different test levels? (unit, integration, e2e)

**Build:**
- Detected: `npm run build` - Correct?
- Or: What command builds the project?

**Typecheck:**
- Detected: `npm run typecheck` - Correct?
- Or: What command checks types?

### 2.3 Conventions

Ask about project-specific conventions:

- Are there naming conventions? (files, functions, components)
- Are there architectural patterns to follow?
- Are there things Claude should NEVER do in this project?
- Are there things Claude should ALWAYS do?

### 2.4 Documentation References

Ask about important files:

- Is there a PRD or roadmap? → Reference with `@.agents/PRD.md`
- Is there architecture documentation? → Reference with `@`
- Are there other important docs?

---

## Phase 3: Generate CLAUDE.md

### Template Structure

```markdown
# {Project Name}

{1-2 sentence description}

## Commands

### Lint
```bash
{lint command}
```

### Test
```bash
# Unit tests
{unit test command}

# Integration tests (if applicable)
{integration test command}

# E2E tests (if applicable)
{e2e test command}
```

### Build
```bash
{build command}
```

### Typecheck
```bash
{typecheck command}
```

## Project Structure

```
{key directories with purpose}
```

## Conventions

### Naming
- {naming convention 1}
- {naming convention 2}

### Patterns
- {pattern to follow}

## Important Rules

### ALWAYS
- {thing to always do}

### NEVER
- {thing to never do}

## Documentation

- Project overview: @README.md
- Roadmap: @.agents/PRD.md (if exists)
- {other important docs}
```

---

## Phase 4: Update Flow (if mode = update)

### 4.1 Read Existing CLAUDE.md

Parse current content and structure.

### 4.2 Ask What to Update

Using AskUserQuestion:

- What should be updated? (Commands, Conventions, Structure, All)
- Any new information to add?
- Anything to remove or change?

### 4.3 Merge Changes

- Keep existing content where applicable
- Update only requested sections
- Add new sections if needed
- Preserve user customizations

---

## Phase 5: Validate & Save

### 5.1 Pre-Save Review

Show generated CLAUDE.md to user:

```
## Preview: CLAUDE.md

{content preview}

---

Save this CLAUDE.md? (yes/no/edit)
```

### 5.2 User Options

| Response | Action |
|----------|--------|
| `yes` | Save to CLAUDE.md |
| `no` | Discard, ask what to change |
| `edit` | User provides specific edits |

### 5.3 Save

Write to `./CLAUDE.md` in project root.

---

## Phase 6: Summary

```markdown
## CLAUDE.md Created

### Detected
- **Tech Stack**: {language/framework}
- **Package Manager**: {npm/pip/cargo/etc}

### Commands Configured
- Lint: `{command}`
- Test: `{command}`
- Build: `{command}`
- Typecheck: `{command}`

### Conventions Added
- {count} naming conventions
- {count} patterns
- {count} rules

### Next Steps
1. Review CLAUDE.md
2. Run `/prd` to create project roadmap
3. Start development with `/prime`
```

---

## Guidelines

### CLAUDE.md Best Practices (Anthropic)

1. **Keep it concise** - Only info Claude can't detect automatically
2. **Focus on commands** - Lint, test, build should be copy-pasteable
3. **Be specific** - "Use camelCase" not "follow conventions"
4. **Reference don't repeat** - Use `@file.md` instead of copying content
5. **Update regularly** - Keep in sync with project changes

### What NOT to Include

- Information obvious from code (language, framework)
- Entire README content (reference instead)
- Long lists of all files
- Generic programming advice

### What TO Include

- Exact commands for lint/test/build
- Project-specific conventions not in config files
- Important rules (ALWAYS/NEVER)
- References to key documentation

---

## Example Usage

```
/create-claude
→ "Detected Node.js project with TypeScript..."
→ "What is this project about?"
→ Interview continues
→ Generates CLAUDE.md
→ "Save this? (yes/no/edit)"

/create-claude update
→ "What would you like to update?"
→ User: "Add new test command"
→ Updates CLAUDE.md
```

---

## Example Output

```markdown
# MyApp

React application for task management with Node.js backend.

## Commands

### Lint
```bash
npm run lint
```

### Test
```bash
# Unit tests
npm run test:unit

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e
```

### Build
```bash
npm run build
```

### Typecheck
```bash
npm run typecheck
```

## Conventions

### Naming
- Components: PascalCase (`UserProfile.tsx`)
- Hooks: camelCase with `use` prefix (`useAuth.ts`)
- Utils: camelCase (`formatDate.ts`)

### Patterns
- Use React Query for data fetching
- Use Zustand for client state
- Follow feature-folder structure

## Important Rules

### ALWAYS
- Run `npm run lint` before committing
- Write tests for new features
- Use TypeScript strict mode

### NEVER
- Commit directly to main
- Use `any` type
- Skip error handling

## Documentation

- Overview: @README.md
- API Docs: @docs/api.md
- Roadmap: @.agents/PRD.md
```
