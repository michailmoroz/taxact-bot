---
name: research
description: Deep dive research on technology or codebase topics
argument-hint: "<topic or question>"
disable-model-invocation: false
user-invocable: true
---

# Research: Deep Dive Investigation

Conduct thorough research on: **$ARGUMENTS**

## Purpose

Use this command when you need deep understanding BEFORE planning:

- **Technology Research**: Libraries, APIs, best practices, implementation approaches
- **Codebase Research**: How existing systems work, patterns, dependencies

For bug investigation and root-cause analysis, use `/debug` instead.

## Process

### Phase 1: Classify Research Type

Determine the research type based on the topic:

| Type | Indicators | Primary Sources |
|------|------------|-----------------|
| **Technology** | "How to...", "Best way to...", external tools/APIs | Web search, docs, examples |
| **Codebase** | "How does X work?", "Where is Y handled?", internal systems | Code files, git history, tests |
| **Mixed** | Internal + external aspects | Both sources |

### Phase 2: Gather Information

#### For Technology Research

1. **Web Search**: Current best practices, official documentation
2. **Compare Options**: If multiple approaches exist, compare pros/cons
3. **Check Compatibility**: Does it work with project's tech stack?
4. **Find Examples**: Reference implementations, code samples

#### For Codebase Research

1. **Find Entry Points**: Where does the relevant code start?
2. **Trace Flow**: Follow data/control flow through the system
3. **Check Tests**: What do tests reveal about expected behavior?
4. **Read History**: `git log` for relevant files - why were changes made?
5. **Map Dependencies**: What does this code depend on? What depends on it?

### Phase 3: Synthesize Findings

Organize findings into actionable insights:

1. **Key Findings**: Most important discoveries
2. **Recommendations**: Suggested approach if applicable
3. **Risks/Caveats**: What to watch out for
4. **Open Questions**: What remains unclear

### Phase 4: Create Research Report

Write report to `.agents/research/{kebab-case-topic}.md`

---

## Output Format

```markdown
# Research: {Topic}

**Date**: {YYYY-MM-DD}
**Type**: Technology | Codebase | Mixed
**Status**: Complete | Partial (needs more investigation)

## Summary

{2-3 sentences: What was investigated and key takeaway}

## Key Findings

### Finding 1: {Title}

{Description with evidence}

- Source: {file:line | URL | git commit}
- Confidence: High | Medium | Low

### Finding 2: {Title}
...

## Evidence

### Code References (for Codebase Research)

| File | Lines | Relevance |
|------|-------|-----------|
| `path/to/file.ts` | 42-67 | {why relevant} |

### External Sources (for Technology Research)

| Source | URL | Key Info |
|--------|-----|----------|
| {Doc/Article name} | {URL} | {what it contributes} |

## Recommendations

{Based on findings, what approach is recommended?}

1. **Recommended**: {approach} because {reason}
2. **Alternative**: {approach} - {tradeoffs}

## Risks & Caveats

- {Risk 1}: {mitigation}
- {Risk 2}: {mitigation}

## Open Questions

- [ ] {Question that couldn't be answered}
- [ ] {Area needing more investigation}

## Next Steps

- [ ] {Suggested follow-up action}
- [ ] Consider `/planning {feature}` if ready to implement
```

---

## Guidelines

### Research Quality

- **Be thorough**: This is a deep dive, not a quick scan
- **Cite sources**: Every finding needs evidence (file:line, URL, commit)
- **Stay focused**: Answer the specific question, don't go on tangents
- **Be honest**: Mark confidence levels, note what's uncertain

### For Technology Research

- Prefer official documentation over blog posts
- Check dates - is the info current?
- Verify compatibility with project's existing stack
- Look for production-ready solutions, not experiments

### For Codebase Research

- Use `git blame` to understand why code exists
- Read tests - they document expected behavior
- Check for comments and docstrings
- Look at recent PRs touching relevant files

### Report Length

- Aim for **200-400 lines** for substantial topics
- Can be shorter for focused questions
- If over 500 lines, consider splitting into sub-topics

---

## After Research

1. **Save** report to `.agents/research/{kebab-case-topic}.md`
2. **Summarize** key findings for the user:
   - 3-5 bullet points of main discoveries
   - Recommended approach if applicable
   - Open questions if any
3. **Suggest next step**:
   - Ready to plan? → `/planning {feature}`
   - Need more info? → What to investigate next
   - Answered the question? → Done

---

## Example Usage

```
/research how authentication works in this codebase

/research best practices for implementing websockets in node.js

/research what libraries are available for PDF generation
```

---

## Example Summary Output

```
## Research Complete: .agents/research/authentication-system.md

### Key Findings

- Auth uses JWT tokens stored in httpOnly cookies
- Session management in `src/auth/session.ts:45-120`
- Refresh token rotation implemented, 7-day expiry
- No rate limiting on login endpoint (potential issue)

### Recommendation

Extend existing auth system rather than replace. Pattern established in `src/auth/` is solid.

### Open Questions

- [ ] How are API keys for service accounts handled?

Ready to plan a feature? Use `/planning {feature-name}`
```
