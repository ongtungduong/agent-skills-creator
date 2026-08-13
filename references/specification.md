# Agent Skills Specification (agentskills.io)

Distilled from https://agentskills.io/specification. This is the normative reference — when in doubt, these rules win.

## Contents

1. [Directory structure](#directory-structure)
2. [SKILL.md format](#skillmd-format)
3. [Frontmatter fields](#frontmatter-fields)
4. [Body content](#body-content)
5. [Optional directories](#optional-directories)
6. [Progressive disclosure](#progressive-disclosure)
7. [File references](#file-references)
8. [Validation](#validation)

## Directory structure

A skill is a directory containing, at minimum, a `SKILL.md` file:

```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── ...               # Any additional files or directories
```

## SKILL.md format

`SKILL.md` must contain YAML frontmatter (delimited by `---` lines) followed by Markdown content.

Minimal valid example:

```markdown
---
name: skill-name
description: A description of what this skill does and when to use it.
---
```

Example with optional fields:

```markdown
---
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Use when handling PDFs.
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
---
```

## Frontmatter fields

| Field           | Required | Constraints |
| --------------- | -------- | ----------- |
| `name`          | Yes      | Max 64 chars. Lowercase letters, numbers, hyphens only. No leading/trailing hyphen. |
| `description`   | Yes      | Max 1024 chars. Non-empty. What the skill does and when to use it. |
| `license`       | No       | License name or reference to a bundled license file. |
| `compatibility` | No       | Max 500 chars. Environment requirements (intended product, system packages, network access, etc.). |
| `metadata`      | No       | Arbitrary string-key → string-value mapping for extra metadata. |
| `allowed-tools` | No       | Space-separated string of pre-approved tools. Experimental. |

### `name`

- 1–64 characters
- Only lowercase alphanumeric characters (`a-z`, `0-9`) and hyphens (`-`)
- Must not start or end with a hyphen
- Must not contain consecutive hyphens (`--`)
- **Must match the parent directory name**

Valid: `pdf-processing`, `data-analysis`, `code-review`
Invalid: `PDF-Processing` (uppercase), `-pdf` (leading hyphen), `pdf--processing` (consecutive hyphens)

### `description`

- 1–1024 characters
- Should describe both **what** the skill does and **when** to use it
- Should include specific keywords that help agents identify relevant tasks

Good:

```yaml
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.
```

Poor:

```yaml
description: Helps with PDFs.
```

### `license`

Keep it short — the name of a license or of a bundled license file:

```yaml
license: Proprietary. LICENSE.txt has complete terms
```

### `compatibility`

- 1–500 characters if provided
- Include **only** if the skill has real environment requirements. Most skills do not need it.

```yaml
compatibility: Designed for Claude Code (or similar products)
compatibility: Requires git, docker, jq, and access to the internet
compatibility: Requires Python 3.14+ and uv
```

### `metadata`

Map from string keys to string values. Clients use it for properties not defined by the spec. Make key names reasonably unique to avoid conflicts.

```yaml
metadata:
  author: example-org
  version: "1.0"
```

### `allowed-tools`

Space-separated string of pre-approved tools. Experimental — support varies between agent implementations.

```yaml
allowed-tools: Bash(git:*) Bash(jq:*) Read
```

## Body content

The Markdown body after the frontmatter contains the skill instructions. There are no format restrictions — write whatever helps agents perform the task effectively.

Recommended sections:

- Step-by-step instructions
- Examples of inputs and outputs
- Common edge cases

The agent loads the entire file once it activates the skill, so split longer content into referenced files.

## Optional directories

### `scripts/`

Executable code agents can run. Scripts should:

- Be self-contained or clearly document dependencies
- Include helpful error messages
- Handle edge cases gracefully

Supported languages depend on the agent implementation; Python, Bash, and JavaScript are common.

### `references/`

Additional documentation agents read when needed — e.g. `REFERENCE.md`, `FORMS.md`, or domain-specific files (`finance.md`, `legal.md`). Keep individual files focused; agents load them on demand, so smaller files mean less context use. Include a table of contents in files over ~300 lines.

### `assets/`

Static resources: templates (document/configuration), images (diagrams, examples), data files (lookup tables, schemas).

## Progressive disclosure

Agents load skills progressively, in three stages:

1. **Metadata** (~100 tokens): `name` and `description` are loaded at startup for all skills
2. **Instructions** (< 5000 tokens recommended): the full `SKILL.md` body loads when the skill activates
3. **Resources** (as needed): files in `scripts/`, `references/`, `assets/` load only when required; scripts can execute without being loaded into context

Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files.

## File references

Reference other files using relative paths from the skill root:

```markdown
See [the reference guide](references/REFERENCE.md) for details.

Run the extraction script:
scripts/extract.py
```

Keep file references one level deep from `SKILL.md`. Avoid deeply nested reference chains.

## Validation

The official reference library:

```bash
skills-ref validate ./my-skill
```

(https://github.com/agentskills/agentskills/tree/main/skills-ref)

This skill also bundles `scripts/validate_skill.py`, a dependency-free validator implementing the same frontmatter and naming rules.
