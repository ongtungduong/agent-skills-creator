#!/usr/bin/env python3
"""Validate an Agent Skill directory against the agentskills.io specification.

Usage: python validate_skill.py <path-to-skill-directory> [--json]

Checks (errors fail validation, warnings do not):
  errors:   SKILL.md present and UTF-8, frontmatter well-formed, name/description present
            and within constraints, name matches directory, compatibility <= 500
            chars, metadata is a flat string->string map
  warnings: unknown frontmatter fields, body over 500 lines, referenced
            scripts//references//assets/ paths that do not exist or escape
            the skill directory (`..`)

Exit codes: 0 = valid, 1 = validation errors, 2 = usage error.
Requires only the Python standard library.
"""
import json
import re
import sys
from pathlib import Path

KNOWN_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
BLOCK_SCALARS = {">", ">-", "|", "|-"}
NON_STRING_RE = re.compile(r"^(true|false|null|~|[-+]?\d+(\.\d+)?)$", re.IGNORECASE)


def valid_name_chars(name):
    """Unicode lowercase alphanumerics and hyphens; no leading/trailing/double hyphen."""
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return False
    return all(ch == "-" or (ch.isalnum() and ch == ch.lower() and not ch.isupper()) for ch in name)


def parse_frontmatter(text):
    """Parse the YAML frontmatter subset the spec uses.

    Handles top-level `key: value` scalars, folded (`>`, `>-`) and literal
    (`|`, `|-`) block scalars, and one nested mapping level (for `metadata:`).
    Returns (dict, error_or_None, body_start_line_index, non_string_meta_keys).
    Values are always strings; unquoted numbers/booleans/null inside a nested
    mapping are reported in non_string_meta_keys.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "SKILL.md must start with a '---' frontmatter delimiter on line 1", 0, []
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, "frontmatter opening '---' has no closing '---'", 0, []

    data = {}
    non_string = []
    current_map_key = None
    map_indent = None
    i = 1
    while i < end:
        raw = lines[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        if ":" not in line:
            return None, f"cannot parse frontmatter line: {raw!r}", end + 1, non_string
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if indent == 0 and value in BLOCK_SCALARS:
            block = []
            while i < end and (not lines[i].strip() or lines[i][0] in " \t"):
                block.append(lines[i])
                i += 1
            while block and not block[-1].strip():
                block.pop()
            pad = min((len(b) - len(b.lstrip()) for b in block if b.strip()), default=0)
            block = [b[pad:].rstrip() if b.strip() else "" for b in block]
            if value[0] == ">":
                paras, cur = [], []
                for b in block:
                    if b:
                        cur.append(b.strip())
                    else:
                        paras.append(" ".join(cur))
                        cur = []
                paras.append(" ".join(cur))
                text_value = "\n".join(paras)
            else:
                text_value = "\n".join(block)
            data[key] = text_value if value.endswith("-") or not text_value else text_value + "\n"
            current_map_key = None
            continue
        quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'"
        if quoted:
            value = value[1:-1]
        if indent == 0:
            if value == "":
                data[key] = {}
                current_map_key = key
                map_indent = None
            else:
                data[key] = value
                current_map_key = None
        else:
            if current_map_key is None:
                return None, f"unexpected indented frontmatter line: {raw!r}", end + 1, non_string
            if map_indent is None:
                map_indent = indent
            elif indent != map_indent:
                return None, f"nested mapping not allowed under {current_map_key!r}: {raw!r}", end + 1, non_string
            if value == "":
                non_string.append(key)
            elif not quoted and NON_STRING_RE.match(value):
                non_string.append(key)
            data[current_map_key][key] = value
    return data, None, end + 1, non_string


def find_missing_references(body, skill_dir):
    """Return (missing, escaping) lists of referenced scripts//references//assets/ paths."""
    missing, escaping = [], []
    seen = set()
    root = skill_dir.resolve()
    for match in re.finditer(r"(?:scripts|references|assets)/[A-Za-z0-9_./-]+", body):
        rel = match.group(0).rstrip(".")
        if rel in seen:
            continue
        seen.add(rel)
        # skip obvious placeholders/examples containing wildcard-ish tokens
        if "*" in rel or "<" in rel:
            continue
        target = (skill_dir / rel).resolve()
        if ".." in rel.split("/") or not target.is_relative_to(root):
            escaping.append(rel)
        elif not target.exists():
            missing.append(rel)
    return missing, escaping


def validate(skill_dir):
    errors, warnings = [], []
    skill_dir = Path(skill_dir)

    if not skill_dir.is_dir():
        return [f"not a directory: {skill_dir}"], []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"missing required file: {skill_md}"], []

    try:
        text = skill_md.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        return [f"cannot read {skill_md} as UTF-8 text: {exc}"], []
    fm, err, body_start, non_string_meta = parse_frontmatter(text)
    if err:
        return [err], []

    # name
    name = fm.get("name")
    if not isinstance(name, str) or not name:
        errors.append("frontmatter field 'name' is required and must be non-empty")
    else:
        if len(name) > 64:
            errors.append(f"'name' exceeds 64 characters ({len(name)})")
        if not valid_name_chars(name):
            errors.append(
                f"'name' ({name!r}) must contain only unicode lowercase letters, digits "
                "and single hyphens, and must not start or end with a hyphen"
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
    elif meta and non_string_meta:
        errors.append(
            "'metadata' values must be strings; quote these values: "
            + ", ".join(repr(k) for k in non_string_meta)
        )

    # allowed-tools / license type sanity
    for field in ("allowed-tools", "license"):
        val = fm.get(field)
        if val is not None and not isinstance(val, str):
            errors.append(f"'{field}' must be a string")

    for key in fm:
        if key not in KNOWN_FIELDS:
            warnings.append(f"unknown frontmatter field {key!r} (not defined by the spec)")

    # body length
    body_lines = text.splitlines()[body_start:]
    if len(body_lines) > 500:
        warnings.append(
            f"SKILL.md body is {len(body_lines)} lines; the spec recommends under 500 "
            "(move detail into references/)"
        )
    body = "\n".join(body_lines)
    if not body.strip():
        warnings.append("SKILL.md has no body content after the frontmatter")

    missing, escaping = find_missing_references(body, skill_dir)
    for rel in missing:
        warnings.append(f"SKILL.md references {rel!r} but that path does not exist")
    for rel in escaping:
        warnings.append(f"SKILL.md reference {rel!r} escapes skill directory")

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
