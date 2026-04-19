---
name: brainstorm
description: >
  Phase 1 of SDD: discovery, problem framing, user stories, and mental model
  building. Auto-activates when invoked via /brainstorm or starting a new
  feature from scratch.
---

# Brainstorm — Phase 1

## Core principle
You cannot design what you don't understand.
Phase 1 ends when you have a complete mental model of the problem,
not when you have a solution.

## Outputs
- Problem statement (1 paragraph, plain English)
- User stories (who, what, why)
- Key constraints and non-goals
- Open questions that must be answered before design
- Suggested stack and approach

## Process
1. Ask clarifying questions until the problem is unambiguous
2. Restate the problem in your own words — confirm with the user
3. List assumptions explicitly
4. Identify what success looks like (measurable)
5. Surface risks early

## Template output
```markdown
## Problem
[One paragraph description]

## Who uses this
- [User A]: needs X because Y
- [User B]: needs X because Y

## Success criteria
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]

## Constraints
- [Technical constraint]
- [Business constraint]

## Non-goals
- [What we are explicitly NOT building]

## Open questions
- [ ] [Question that must be answered before Phase 2]
```

## Gate
Phase 1 is complete when the user confirms the mental model is accurate.
Do NOT proceed to Phase 2 without explicit approval.
