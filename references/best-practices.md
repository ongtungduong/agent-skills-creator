# Best Practices for Skill Creators

Distilled from https://agentskills.io/skill-creation/best-practices. Read this when writing or reviewing the body of any non-trivial skill.

## Contents

1. [Start from real expertise](#start-from-real-expertise)
2. [Refine with real execution](#refine-with-real-execution)
3. [Spend context wisely](#spend-context-wisely)
4. [Calibrate control](#calibrate-control)
5. [Patterns for effective instructions](#patterns-for-effective-instructions)
6. [Optimizing the description](#optimizing-the-description)

## Start from real expertise

The most common pitfall: generating a skill from an LLM's general training knowledge alone. The result is vague, generic procedure ("handle errors appropriately," "follow best practices") instead of the specific API patterns, edge cases, and conventions that make a skill valuable.

Two ways to ground a skill in real expertise:

**Extract from a hands-on task.** Complete a real task in conversation first, then extract the reusable pattern. Mine: the steps that worked, the corrections the user made ("use library X instead of Y", "check for edge case Z"), input/output formats, and the context the user had to supply that the agent didn't know.

**Synthesize from existing artifacts.** Feed real project material into the creation process: internal docs, runbooks, style guides, API specs, schemas, config files, code-review comments, issue trackers, version-control history (patches reveal recurring fixes), and real failure cases with their resolutions. A skill synthesized from your team's actual incident reports beats one synthesized from a generic best-practices article.

## Refine with real execution

First drafts need refinement. Run the skill against real tasks and feed all results — not just failures — back in. Ask: what triggered false positives? What was missed? What could be cut? Even one execute-then-revise pass noticeably improves quality.

Read execution **traces**, not just final outputs. If the agent wastes turns, common causes are:

- Instructions too vague (the agent tries several approaches before one works)
- Instructions that don't apply to the current task (the agent follows them anyway)
- Too many options with no clear default

## Spend context wisely

Once activated, the full `SKILL.md` body competes for attention with conversation history, system context, and other active skills.

**Add what the agent lacks, omit what it knows.** Don't explain what a PDF is or how HTTP works. Jump straight to the non-obvious:

```markdown
<!-- Too verbose -->
PDF (Portable Document Format) files are a common file format... To extract
text you'll need a library. pdfplumber is recommended because...

<!-- Better -->
Use pdfplumber for text extraction. For scanned documents, fall back to
pdf2image with pytesseract.
```

Test each piece of content with: "Would the agent get this wrong without this instruction?" If no, cut it. If the agent handles the entire task well without the skill, the skill may not be adding value.

**Design coherent units.** Scope a skill like a function: one coherent unit of work that composes with other skills. Too narrow → several skills must load per task, risking overhead and conflicts. Too broad → hard to activate precisely. Querying a database and formatting results = one unit; adding database administration = too much.

**Aim for moderate detail.** Exhaustive documentation hurts: the agent struggles to find what's relevant and follows inapplicable instructions. Concise stepwise guidance plus one working example outperforms covering every edge case — leave most edge cases to the agent's judgment.

**Structure large skills with progressive disclosure.** Keep `SKILL.md` under 500 lines / 5000 tokens. Move detail to `references/`. Crucially, tell the agent **when** to load each file: "Read `references/api-errors.md` if the API returns a non-200 status" beats "see references/ for details".

## Calibrate control

Match instruction specificity to task fragility. Most skills mix both modes — calibrate each part independently.

**Give freedom** when multiple approaches are valid. Explaining *why* beats rigid directives — an agent that understands purpose makes better context-dependent decisions:

```markdown
## Code review process
1. Check all database queries for SQL injection (use parameterized queries)
2. Verify authentication checks on every endpoint
3. Look for race conditions in concurrent code paths
4. Confirm error messages don't leak internal details
```

**Be prescriptive** when operations are fragile, consistency matters, or an exact sequence is required:

```markdown
## Database migration
Run exactly this sequence:
    python scripts/migrate.py --verify --backup
Do not modify the command or add additional flags.
```

**Provide defaults, not menus.** Pick a default; mention alternatives only as an escape hatch:

```markdown
<!-- Too many options -->
You can use pypdf, pdfplumber, PyMuPDF, or pdf2image...

<!-- Clear default with escape hatch -->
Use pdfplumber for text extraction. For scanned PDFs requiring OCR,
use pdf2image with pytesseract instead.
```

**Favor procedures over declarations.** Teach how to approach a class of problems, not what to produce for one instance:

```markdown
<!-- Specific answer — only useful once -->
Join `orders` to `customers` on `customer_id`, filter region = 'EMEA', sum `amount`.

<!-- Reusable method -->
1. Read the schema from `references/schema.yaml` to find relevant tables
2. Join tables using the `_id` foreign key convention
3. Apply filters from the user's request as WHERE clauses
4. Aggregate numeric columns and format as a markdown table
```

Specific details are still fine where they're the point: output templates, hard constraints ("never output PII"), exact tool invocations. The *approach* should generalize.

If you catch yourself writing ALWAYS/NEVER in all caps or building rigid scaffolding, treat it as a yellow flag: usually the underlying reason is missing. State the reason instead.

## Patterns for effective instructions

Reusable techniques — use the ones that fit.

### Gotchas section

Often the highest-value content: environment-specific facts that defy reasonable assumptions. Concrete corrections, not general advice:

```markdown
## Gotchas
- The `users` table uses soft deletes. Queries must include
  `WHERE deleted_at IS NULL` or results include deactivated accounts.
- The user ID is `user_id` in the database, `uid` in the auth service,
  and `accountId` in the billing API. All three are the same value.
- `/health` returns 200 whenever the web server runs, even if the DB is
  down. Use `/ready` for full service health.
```

Keep gotchas in `SKILL.md` itself — the agent must read them *before* hitting the situation; it may not recognize the trigger to load a reference file. When an agent makes a mistake you correct, add the correction here — the most direct iterative improvement.

### Templates for output format

Provide a concrete template rather than prose describing the format — agents pattern-match well against structure. Short templates inline; long or conditional ones in `assets/`:

```markdown
## Report structure
Use this template, adapting sections as needed:

# [Analysis Title]
## Executive summary
[One-paragraph overview]
## Key findings
- Finding 1 with supporting data
## Recommendations
1. Specific actionable recommendation
```

### Checklists for multi-step workflows

An explicit checklist helps the agent track progress and not skip steps, especially with dependencies or validation gates:

```markdown
Progress:
- [ ] Step 1: Analyze the form (run `scripts/analyze_form.py`)
- [ ] Step 2: Create field mapping (edit `fields.json`)
- [ ] Step 3: Validate mapping (run `scripts/validate_fields.py`)
- [ ] Step 4: Fill the form (run `scripts/fill_form.py`)
```

### Validation loops

Do the work → run a validator (script, reference checklist, or self-check) → fix → repeat until it passes. A reference document can serve as the validator: "check your work against the reference before finalizing."

### Plan-validate-execute

For batch or destructive operations: produce an intermediate plan in a structured format, validate it against a source of truth, only then execute.

```markdown
1. Extract form fields: `python scripts/analyze_form.py input.pdf` → form_fields.json
2. Create field_values.json mapping each field to its intended value
3. Validate: `python scripts/validate_fields.py form_fields.json field_values.json`
4. If validation fails, revise field_values.json and re-validate
5. Fill: `python scripts/fill_form.py input.pdf field_values.json output.pdf`
```

The key is step 3: errors like "Field 'signature_date' not found — available fields: customer_name, order_total, signature_date_signed" let the agent self-correct.

### Bundling reusable scripts

When test-run traces show the agent reinventing the same logic each run (building charts, parsing a format, validating output), write it once, test it, and bundle it in `scripts/`.

## Optimizing the description

The `description` is the primary triggering mechanism — the only text visible when the agent decides whether to activate the skill.

- State **what** the skill does AND **when** to use it, in the same field. All "when to use" information belongs in the description, not the body.
- Include the concrete keywords, file types, and phrasings real user requests would contain.
- Agents tend to *under*-trigger skills, so lean pushy: "Use whenever the user mentions X, Y, Z — even if they don't explicitly ask for W."
- Test triggering against both should-trigger prompts (varied phrasings, casual/typo'd wording, cases that don't name the skill) and near-miss should-NOT-trigger prompts (adjacent domains sharing keywords). See https://agentskills.io/skill-creation/optimizing-descriptions for a systematic loop.
