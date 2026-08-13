#!/usr/bin/env python3
"""Validate an Agent Skill directory against the agentskills.io specification.

Usage: python validate_skill.py <path-to-skill-directory> [--json]

Checks (errors fail validation, warnings do not):
  errors:   SKILL.md present, frontmatter well-formed, name/description present
            and within constraints, name matches directory, compatibility <= 500
            chars, metadata is a flat string->string map
  warnings: unknown frontmatter fields, body over 500 lines, referenced
            scripts//references//assets/ paths that do not exist

Exit codes: 0 = valid, 1 = validation errors, 2 = usage error.
Requires only the Python standard library.
"""
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KNOWN_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def parse_frontmatter(text):
    """Parse the YAML frontmatter subset the spec uses.

    Handles top-level `key: value` scalars and one nested mapping level
    (for `metadata:`). Returns (dict, error_string_or_None).
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "SKILL.md must start with a '---' frontmatter delimiter on line 1"
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, "frontmatter opening '---' has no closing '---'"

    data = {}
    current_map_key = None
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        if ":" not in line:
            return None, f"cannot parse frontmatter line: {raw!r}"
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        # strip matching quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if indent == 0:
            if value == "":
                data[key] = {}
                current_map_key = key
            else:
                data[key] = value
                current_map_key = None
        else:
            if current_map_key is None:
                return None, f"unexpected indented frontmatter line: {raw!r}"
            data[current_map_key][key] = value
    return data, None


def find_missing_references(body, skill_dir):
    """Return referenced scripts//references//assets/ paths that don't exist."""
    missing = []
    seen = set()
    for match in re.finditer(r"(?:scripts|references|assets)/[A-Za-z0-9_./-]+", body):
        rel = match.group(0).rstrip(".")
        if rel in seen:
            continue
        seen.add(rel)
        # skip obvious placeholders/examples containing wildcard-ish tokens
        if "*" in rel or "<" in rel:
            continue
        if not (skill_dir / rel).exists():
            missing.append(rel)
    return missing


def validate(skill_dir):
    errors, warnings = [], []
    skill_dir = Path(skill_dir)

    if not skill_dir.is_dir():
        return [f"not a directory: {skill_dir}"], []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"missing required file: {skill_md}"], []

    text = skill_md.read_text(encoding="utf-8")
    fm, err = parse_frontmatter(text)
    if err:
        return [err], []

    # name
    name = fm.get("name")
    if not isinstance(name, str) or not name:
        errors.append("frontmatter field 'name' is required and must be non-empty")
    else:
        if len(name) > 64:
            errors.append(f"'name' exceeds 64 characters ({len(name)})")
        if not NAME_RE.match(name):
            errors.append(
                f"'name' ({name!r}) must contain only lowercase a-z, 0-9 and single "
                "hyphens, and must not start or end with a hyphen"
            )
        if name != skill_dir.resolve().name:
            errors.append(
                f"'name' ({name!r}) must match the skill directory name "
                f"({skill_dir.resolve().name!r})"
            )

    # description
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc:
        errors.append("frontmatter field 'description' is required and must be non-empty")
    elif len(desc) > 1024:
        errors.append(f"'description' exceeds 1024 characters ({len(desc)})")

    # compatibility
    compat = fm.get("compatibility")
    if compat is not None:
        if not isinstance(compat, str) or not compat:
            errors.append("'compatibility' must be a non-empty string when present")
        elif len(compat) > 500:
            errors.append(f"'compatibility' exceeds 500 characters ({len(compat)})")

    # metadata
    meta = fm.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        errors.append("'metadata' must be a mapping of string keys to string values")

    # allowed-tools / license type sanity
    for field in ("allowed-tools", "license"):
        val = fm.get(field)
        if val is not None and not isinstance(val, str):
            errors.append(f"'{field}' must be a string")

    for key in fm:
        if key not in KNOWN_FIELDS:
            warnings.append(f"unknown frontmatter field {key!r} (not defined by the spec)")

    # body length
    body_start = text.splitlines().index("---", 1) if "---" in text.splitlines()[1:] else 0
    body_lines = text.splitlines()[body_start + 1:]
    if len(body_lines) > 500:
        warnings.append(
            f"SKILL.md body is {len(body_lines)} lines; the spec recommends under 500 "
            "(move detail into references/)"
        )
    body = "\n".join(body_lines)
    if not body.strip():
        warnings.append("SKILL.md has no body content after the frontmatter")

    for rel in find_missing_references(body, skill_dir):
        warnings.append(f"SKILL.md references {rel!r} but that path does not exist")

    return errors, warnings


def main(argv):
    args = [a for a in argv[1:] if a != "--json"]
    as_json = "--json" in argv
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    errors, warnings = validate(args[0])
    if as_json:
        print(json.dumps({"valid": not errors, "errors": errors, "warnings": warnings}, indent=2))
    else:
        for e in errors:
            print(f"ERROR: {e}")
        for w in warnings:
            print(f"WARNING: {w}")
        print("PASS" if not errors else "FAIL", f"({len(errors)} errors, {len(warnings)} warnings)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
