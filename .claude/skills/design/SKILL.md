---
name: design
description: >
  Phase 3 of SDD: architecture, file manifest, component design.
  Auto-activates when invoked via /design or transitioning from
  requirements to implementation planning.
---

# Design — Phase 3

## Core principle
The file manifest is the design.
If you can't name every file you'll create and describe its responsibility,
you don't understand the design yet.

## Outputs
- File manifest (path, responsibility, key exports)
- Component diagram (text-based, simple)
- Data flow description
- External dependencies list
- Migration or setup steps

## Template
```markdown
## File Manifest

### New files
| File | Responsibility |
|------|----------------|
| `src/module/feature.py` | [one line] |

### Modified files
| File | Change |
|------|--------|
| `src/module/models.py` | Add FeatureOutput model |

## Data flow
[Input] → [Component A] → [Component B] → [Output]

## Dependencies
- `library>=1.0` — used for X

## Setup steps
1. [Step 1]
2. [Step 2]
```

## Gate
User explicitly approves the file manifest before any code is written.
Do NOT proceed to Phase 4 without approval.
