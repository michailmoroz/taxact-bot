---
description: Commit and push changes based on execution report
argument-hint: <execution-report-path>
---

# Commit: Git Commit + Push

Commit and push changes based on execution report: **$ARGUMENTS**

---

## Phase 0: Pre-Flight Check

Run these checks before proceeding:

### 0.1 Git Repository

```bash
git rev-parse --git-dir
```

| Result | Action |
|--------|--------|
| ✓ Success | Continue |
| ✗ Not a repo | Stop: "This is not a Git repository. Run `git init` first." |

### 0.2 Remote Connection

```bash
git remote -v
```

| Result | Action |
|--------|--------|
| ✓ Remote exists | Continue |
| ✗ No remote | Stop: "No remote configured. Run `git remote add origin <url>`" |

### 0.3 Authentication Check

**For GitHub:**
```bash
gh auth status
```

**For GitLab:**
```bash
glab auth status
```

| Result | Action |
|--------|--------|
| ✓ Logged in | Continue |
| ✗ Not logged in | Stop: "Not authenticated. Run `gh auth login` or `glab auth login`" |

### 0.4 Uncommitted Changes

```bash
git status --porcelain
```

| Result | Action |
|--------|--------|
| ✓ Changes exist | Continue |
| ✗ No changes | Stop: "Nothing to commit. Working tree clean." |

### 0.5 Current Branch

```bash
git branch --show-current
```

Display current branch for user awareness.

---

## Phase 1: Read Context

### 1.1 Read Execution Report

Read the execution report from: `$ARGUMENTS`

Extract:
- **Feature Name**: From report title
- **Files Created**: List
- **Files Modified**: List
- **Tests Added**: List
- **Summary**: What was implemented

### 1.2 Get Git Diff

```bash
git diff --stat
git diff --cached --stat
```

Understand what files changed and how much.

---

## Phase 2: Generate Commit Message

Generate a commit message following **Conventional Commits** format:

```
<type>(<scope>): <description>

<body>

<footer>
```

### Types

| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `docs` | Documentation changes |
| `chore` | Maintenance, dependencies |

### Example Message

```
feat(auth): Add user authentication

- Created auth.service.ts, login.component.ts
- Modified app.module.ts, routes.ts
- Added 5 unit tests, 2 integration tests

Based on: .agents/plans/add-user-authentication.md
Report: .agents/execution-reports/add-user-authentication-2025-02-11.md
```

---

## Phase 3: User Confirmation

**Show to user:**

```
## Commit Summary

**Branch:** main
**Files:** X files changed

### Commit Message:
---
<generated message>
---

### Files to be committed:
- path/to/file1.ts (created)
- path/to/file2.ts (modified)
...

Proceed with commit and push? (y/n)
```

**Wait for user confirmation before proceeding.**

---

## Phase 4: Commit

### 4.1 Stage All Changes

```bash
git add .
```

Or stage specific files if user prefers selective commit.

### 4.2 Commit

```bash
git commit -m "<generated message>"
```

**Use HEREDOC for multi-line messages:**

```bash
git commit -m "$(cat <<'EOF'
feat(auth): Add user authentication

- Created auth.service.ts
- Modified routes.ts
- Added tests

Based on: .agents/plans/add-user-authentication.md
EOF
)"
```

---

## Phase 5: Push

### 5.1 Push to Remote

```bash
git push origin <current-branch>
```

### 5.2 Handle Push Errors

| Error | Action |
|-------|--------|
| Rejected (behind remote) | `git pull --rebase` then retry push |
| Authentication failed | Stop: "Authentication failed. Re-run `gh auth login`" |
| Permission denied | Stop: "Permission denied. Check repository access." |

---

## Phase 6: Summary

Report to user:

```
## Commit Complete

**Commit:** <hash>
**Branch:** main
**Remote:** origin

### Changes pushed:
- X files created
- Y files modified
- Z tests added

### Links:
- Repository: <repo-url>
- Commit: <commit-url>

### Next Steps:
- Monitor CI/CD pipeline
- Verify deployment (if applicable)
```

---

## Error Handling

| Error | Action |
|-------|--------|
| Execution report not found | "Report not found at `$ARGUMENTS`. Check path." |
| Merge conflicts | Stop: "Merge conflicts detected. Resolve manually." |
| Pre-commit hook fails | Show error, ask user to fix |
| Push rejected | Show reason, suggest resolution |

---

## Guidelines

### Commit Messages
- Use imperative mood ("Add feature" not "Added feature")
- First line max 72 characters
- Reference plan and execution report in body
- Follow project conventions from CLAUDE.md

### Safety
- Always show user what will be committed
- Wait for confirmation before push
- Never force push without explicit user request
- Never amend pushed commits without user request

### Git Best Practices
- Commit only related changes together
- Keep commits atomic and focused
- Include relevant context in commit body
