---
name: agent-skills-creator
description: Create, review, fix, and validate Agent Skills that conform to the agentskills.io specification. Use whenever the user wants to create a new agent skill, write or edit a SKILL.md, turn a workflow, prompt, or documentation into a reusable skill, restructure an oversized skill, or check a skill against the spec — even if they just say "make a skill for X" or mention agentskills.io, skill folders, or SKILL.md.
license: MIT
metadata:
  author: ongtungduong
  version: "1.0"
  spec: https://agentskills.io/specification
---

# Agent Skills Creator

Create agent skills that conform to the [agentskills.io specification](https://agentskills.io/specification). A skill is a directory containing a `SKILL.md` file (YAML frontmatter + Markdown instructions), optionally bundling `scripts/`, `references/`, and `assets/`.

## Workflow

Follow these steps in order. Steps 1–2 shape everything else — don't skip them.

### 1. Capture intent

Before writing anything, establish:

- **What** should the skill enable an agent to do? One coherent unit of work — like a well-scoped function. Too narrow forces multiple skills to load per task; too broad activates imprecisely.
- **When** should it trigger? Collect the phrases and contexts a real user would type.
- **What context does the agent lack?** The skill's value is exactly the knowledge the agent wouldn't have on its own: project conventions, specific APIs, non-obvious gotchas, exact command sequences. If the agent already handles the task well without the skill, the skill adds no value.

If the conversation already contains a worked example (the user just did the task manually, or says "turn this into a skill"), mine it: the steps that worked, the corrections the user made, input/output formats, and context the user had to supply. Ask the user to fill gaps rather than inventing generic content — vague filler ("follow best practices", "handle errors appropriately") makes a skill worthless.

### 2. Design the structure

Decide what goes where using progressive disclosure (three loading levels):

| Level | What | Budget |
|---|---|---|
| 1. Metadata | `name` + `description` — always in context | ~100 tokens |
| 2. Instructions | `SKILL.md` body — loaded on activation | < 5000 tokens, < 500 lines |
| 3. Resources | `scripts/`, `references/`, `assets/` — loaded/run on demand | unlimited |

- Core workflow, defaults, and gotchas go in `SKILL.md`.
- Detailed reference material goes in `references/`, split by domain (one file per variant/framework so the agent reads only what's relevant).
- Reusable, deterministic logic goes in `scripts/`. If the agent would rewrite the same helper on every run, bundle it once instead.
- Templates and static files the output needs go in `assets/`.
- Every reference to a bundled file must say **when** to load it ("Read the API-errors reference if the API returns a non-200 status"), use a relative path from the skill root, and stay one level deep — no chains of references.

### 3. Write the frontmatter

When scaffolding a brand-new skill, copy [assets/SKILL-template.md](assets/SKILL-template.md) into `<skill-name>/SKILL.md` as the starting point and replace the bracketed placeholders.

The frontmatter rules are strict — validate them exactly. Full field-by-field rules with examples are in [references/specification.md](references/specification.md); read it before writing frontmatter for the first time in a session.

The two required fields:

- **`name`** — 1–64 chars, only unicode lowercase letters, digits (`a-z`, `0-9`, `é`…), and hyphens; must not start/end with a hyphen or contain `--`; **must equal the skill's directory name**.
- **`description`** — 1–1024 chars. Must state both *what the skill does* and *when to use it*, with the concrete keywords a user's request would contain. This is the only text the agent sees when deciding to activate the skill, so make it slightly pushy: enumerate trigger phrases, file types, and situations. "Helps with PDFs" is a failing description; "Extracts text and tables from PDF files, fills forms, merges PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction" passes.

Optional fields: `license`, `compatibility` (≤500 chars, only for real environment requirements — most skills don't need it), `metadata` (string→string map, e.g. author/version), `allowed-tools` (experimental).

### 4. Write the body

There are no format restrictions on the body — write whatever makes the agent perform well. Principles that consistently matter (full detail with before/after examples in [references/best-practices.md](references/best-practices.md) — read it when writing a body of any complexity):

- **Add what the agent lacks, omit what it knows.** Never explain what a PDF or HTTP is. For each paragraph ask: "Would the agent get this wrong without it?" If no, cut it.
- **Calibrate control to fragility.** Where many approaches work, explain the *why* and let the agent decide. Where operations are fragile or a sequence matters, be exactly prescriptive ("Run exactly this command; do not add flags").
- **Provide defaults, not menus.** Pick one tool/approach; mention alternatives only as an escape hatch for named cases.
- **Teach procedures, not answers.** Instructions should generalize to the whole class of tasks, not solve one instance.
- **Use the proven patterns where they fit:** a Gotchas section for environment facts that defy assumptions; concrete output templates instead of prose descriptions of formats; checklists for multi-step workflows; validate-fix-repeat loops; plan-validate-execute for batch or destructive operations.

If the skill bundles executable code, read [references/scripts-guide.md](references/scripts-guide.md) for how to make scripts self-contained (PEP 723 / `npm:` specifiers), non-interactive, and agent-friendly (structured stdout, helpful errors, `--help`, idempotency).

### 5. Validate

Run the bundled validator on the finished skill directory:

```bash
python scripts/validate_skill.py <path-to-skill-directory>
```

It checks every frontmatter constraint from the spec (name format, name↔directory match, description/compatibility lengths, metadata shape), warns when the body exceeds 500 lines, and warns about referenced `scripts/`/`references/`/`assets/` paths that don't exist. Fix all errors and review every warning before delivering. If the environment has the official reference tool available, `skills-ref validate <dir>` is an equivalent check.

### 6. Review with fresh eyes

Reread the draft as if you were an agent seeing it cold, mid-task, with a full context window:

- Does the description alone tell you when to activate?
- Can you execute the workflow without asking questions the SKILL.md should have answered?
- Is anything present that you'd already know without the skill? Cut it.
- Are ALL-CAPS MUSTs standing in for missing explanations? Replace with the reason.

Then, if possible, refine with real execution: run the skill against 2–3 realistic tasks and feed the traces back. See [evaluating skills](https://agentskills.io/skill-creation/evaluating-skills) and [optimizing descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) for systematic loops. Wasted agent turns usually mean instructions are vague, inapplicable, or offer too many options.

## Output checklist

Before delivering a skill, confirm:

- [ ] Directory name == `name` frontmatter field
- [ ] `description` states what + when, with trigger keywords
- [ ] `SKILL.md` body under 500 lines; overflow moved to `references/`
- [ ] Every bundled-file mention says when to load it, uses a relative path
- [ ] Scripts (if any) are non-interactive, self-contained, with helpful errors
- [ ] `python scripts/validate_skill.py <dir>` passes with no errors
