# Agent Skills Creator

`agent-skills-creator` is an Agent Skill that teaches how to create, review, and validate other Agent Skills following the [agentskills.io specification](https://agentskills.io). It is a **documentation + tooling** package (not a runtime system) and dogfoods the very principles it teaches — progressive disclosure, effective instruction writing patterns, and automated validation.

**Audience**: Skill creators/reviewers, and any agent harness (Claude Code, Agent SDK, etc.) capable of loading skills from directories.

## Quick Start

1. **Use the skill**: Copy the `agent-skills-creator` folder into your harness's skills directory — ready for immediate activation.
2. **Create a new skill** following the 6 steps in `SKILL.md`:
   1. *Capture intent* — What the skill enables the agent to do, when to activate it, and what context the agent is missing.
   2. *Design structure* — What goes into `SKILL.md`, and what goes into `references/`, `assets/`, or `scripts/`.
   3. *Write frontmatter* — Fill in `name` and `description` (required), using [assets/SKILL-template.md](assets/SKILL-template.md) as a starting point.
   4. *Write the body* — Write only what the agent lacks, applying proven patterns.
   5. *Validate* — Run the validator; it must exit with code 0.
   6. *Review* — Re-read with a fresh perspective and refine based on practical testing.
3. **Validate**:
   ```bash
   python scripts/validate_skill.py /path/to/your/skill
   ```
   Exit codes: `0` valid (warnings do not block) · `1` error found · `2` invalid arguments.

## Directory Structure

```
agent-skills-creator/
├── SKILL.md                  # Core skill — 6-step workflow
├── references/                # One-level deep, no nested subdirectories
│   ├── specification.md       # agentskills.io spec rules — read in Step 3
│   ├── best-practices.md      # Instruction writing patterns — read in Step 4
│   └── scripts-guide.md       # Bundling executable code — read in Step 4 (if using scripts)
├── assets/SKILL-template.md   # Template for new SKILL.md files
└── scripts/validate_skill.py  # Validator tool using Python stdlib only
```

At minimum, every skill requires `SKILL.md`; `references/`, `assets/`, and `scripts/` are optional. All file references within `SKILL.md` must use relative paths, explicitly state **when** to read them, and avoid chaining through multiple nested directory levels.

## Progressive Disclosure

| Tier | Content | Loading Trigger | Token/Size Budget |
|---|---|---|---|
| 1 | Metadata (`name` + `description`) | Startup (all skills) | ~100 tokens |
| 2 | Body of `SKILL.md` | When skill is activated | < 5,000 tokens / < 500 lines |
| 3 | `scripts/`, `references/`, `assets/` | On demand, when specified by workflow | Unlimited |

The agent only loads content when needed — keeping context overhead minimal and avoiding distraction during workflow execution.

## Frontmatter

```yaml
name: your-skill-name         # Required: kebab-case, 1–64 chars, MUST match directory name
description: What + when...   # Required: 1–1024 chars, clearly states what skill does and when to use it
license: MIT                   # Optional
compatibility: Requires ...    # Optional, ≤500 chars — only for actual environment constraints
metadata:                      # Optional: flat string->string map, no nesting
  author: your-name
  version: "1.0"
allowed-tools: Bash(git:*) Read # Optional, experimental
```

`name` cannot contain uppercase letters, spaces, leading/trailing hyphens, or double hyphens (`--`). Full details: [references/specification.md](references/specification.md).

## Validator

`scripts/validate_skill.py <skill-dir> [--json]` — Built with Python stdlib, no external dependencies.

- **Errors (blocking)**: Missing `SKILL.md` · invalid YAML frontmatter · missing or invalid `name`/`description` · `name` does not match directory name · `compatibility` > 500 characters · `metadata` is not a flat string map.
- **Warnings (non-blocking)**: Unknown frontmatter fields · body > 500 lines · reference to non-existent files in `scripts/`, `references/`, or `assets/`.

## Skill Writing Principles

- **Add what the agent lacks, omit what it already knows** — Avoid explaining general concepts like HTTP/JSON; provide repository-specific conventions, gotchas, and exact command sequences.
- **Calibrate control based on fragility** — If multiple approaches work, explain *why* and let the agent decide; for fragile or ordered operations, provide absolute, step-by-step instructions.
- **Provide defaults, not menus** — Pick a recommended default path, mentioning alternatives only for exceptional cases.
- **Agent scripts** (when bundling `scripts/`): Self-contained (PEP 723 for Python or equivalent), non-interactive (no `input()` prompts), include `--help`, output structured data (JSON/CSV), use clear exit codes (`0` success, `1` runtime error, `2` argument/usage error), and provide error messages stating cause + fix.
- **Useful patterns**: A *Gotchas* section for environment-specific quirks; concrete *output templates* instead of prose descriptions; multi-step workflow checklists; validate–fix–repeat loops.

Minimal example:

```yaml
---
name: hello-world
description: Prints a greeting. Use this skill when the user asks for a simple greeting.
---
# Hello World
Say hello to the user.
## Workflow
1. Ask the user for their name
2. Print a personalized greeting
```

## Status

**v1.0** — Complete, passes self-validation (`python scripts/validate_skill.py .` → exit 0). Known limitations: This skill teaches *creating* skills, not operating skills within a specific product application; the validator strictly uses Python stdlib (a trade-off for zero external dependencies and portability); content reflects the standardized agentskills.io spec at the time of writing — updates may be needed if the base specification evolves.

## Contributing

Describe specific issues (spec discrepancies, validator bugs, missing instructions) with supporting evidence (example skills, error traces). Base proposals on real-world use cases rather than speculation.

## License

MIT. See frontmatter in `SKILL.md`.

---
**Author**: ongtungduong · **Version**: 1.0 · **Updated**: 2026-08-13 · Spec: [agentskills.io/specification](https://agentskills.io/specification)
