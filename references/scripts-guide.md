# Using Scripts in Skills

Distilled from https://agentskills.io/skill-creation/using-scripts. Read this when the skill you're creating bundles executable code or shell commands.

## Contents

1. [One-off commands](#one-off-commands)
2. [Referencing scripts from SKILL.md](#referencing-scripts-from-skillmd)
3. [Self-contained scripts](#self-contained-scripts)
4. [Designing scripts for agentic use](#designing-scripts-for-agentic-use)

## One-off commands

When an existing package already does the job, reference it directly in `SKILL.md` — no `scripts/` needed. Prefer runners that auto-resolve dependencies:

| Runner                | Example                                               | Notes                                             |
| --------------------- | ----------------------------------------------------- | ------------------------------------------------- |
| `uvx` (Python)      | `uvx ruff@0.8.0 check .`                            | Fast, aggressive caching; requires uv installed   |
| `pipx run` (Python) | `pipx run 'black==24.10.0' .`                       | Mature alternative; broad OS package availability |
| `npx` (Node)        | `npx eslint@9 --fix .`                              | Ships with npm; pin versions for reproducibility  |
| `bunx` (Bun)        | `bunx eslint@9 --fix .`                             | Only when the environment has Bun                 |
| `deno run`          | `deno run npm:eslint@9 -- --fix .`                  | Needs permission flags (`--allow-read` etc.)    |
| `go run`            | `go run golang.org/x/tools/cmd/goimports@v0.28.0 .` | Built into Go                                     |

Tips:

- **Pin versions** (`npx eslint@9.0.0`) so behavior is stable over time.
- **State prerequisites** in `SKILL.md` ("Requires Node.js 18+"); use the `compatibility` frontmatter field for runtime-level requirements.
- **Move complex commands into scripts.** A one-off command suits a tool with a few flags; once it's hard to get right first try, a tested script in `scripts/` is more reliable.

## Referencing scripts from SKILL.md

Use relative paths from the skill directory root — the agent runs commands from there. List available scripts so the agent knows they exist:

```markdown
## Available scripts

- **`scripts/validate.sh`** — Validates configuration files
- **`scripts/process.py`** — Processes input data

## Workflow

1. Run validation: `bash scripts/validate.sh "$INPUT_FILE"`
2. Process results: `python3 scripts/process.py --input results.json`
```

The same relative-path convention applies inside `references/*.md`.

## Self-contained scripts

Bundle reusable logic in `scripts/` with dependencies declared **inline**, so one command runs it — no manifest or install step.

**Python — PEP 723** inline metadata, run with `uv run scripts/extract.py` (pipx also supports it):

```python
# /// script
# dependencies = [
#   "beautifulsoup4>=4.12,<5",
# ]
# ///
from bs4 import BeautifulSoup
...
```

Pin versions with PEP 508 specifiers; use `requires-python` to constrain the Python version; `uv lock --script` for full reproducibility. If the script needs only the standard library, plain `python3 scripts/x.py` is the most portable option of all.

**Deno** — `npm:`/`jsr:` import specifiers make scripts self-contained by default: `import * as cheerio from "npm:cheerio@1.0.0"`. Packages with native addons may not work.

**Bun** — auto-installs missing packages at runtime; pin versions in the import path (`import * as cheerio from "cheerio@1.0.0"`). Disabled if a `node_modules` exists up the tree.

**Ruby** — `require 'bundler/inline'` with a `gemfile do ... end` block. Pin versions explicitly; there is no lockfile.

## Designing scripts for agentic use

The agent reads stdout/stderr to decide its next move. Design for that:

**Never prompt interactively.** Agents run in non-interactive shells; a TTY prompt hangs forever. Accept all input via flags, env vars, or stdin — and when a required flag is missing, fail with usage guidance:

```
Error: --env is required. Options: development, staging, production.
Usage: python scripts/deploy.py --env staging --tag v1.2.3
```

**Document usage with `--help`.** It's how the agent learns the interface: brief description, flags, examples. Keep it concise — it enters the context window.

**Write helpful error messages.** Say what went wrong, what was expected, what to try: `Error: --format must be one of: json, csv, table. Received: "xml"` — an opaque "invalid input" wastes a turn.

**Use structured output.** Prefer JSON/CSV/TSV over aligned free-form text — parseable by the agent and by `jq`/`cut`/`awk`. Send data to stdout, diagnostics (progress, warnings) to stderr.

**Further considerations:**

- **Idempotency** — agents retry; "create if not exists" beats "fail on duplicate".
- **Input constraints** — reject ambiguous input with a clear error; use enums/closed sets.
- **Dry-run** — for destructive/stateful operations, offer `--dry-run`.
- **Meaningful exit codes** — distinct codes per failure type, documented in `--help`.
- **Safe defaults** — destructive operations may warrant `--confirm`/`--force` gates.
- **Predictable output size** — harnesses truncate large tool output (often 10–30K chars). Default to a summary; support `--offset`/pagination or a required `--output` flag (file path, or `-` to opt into stdout) for large results.
