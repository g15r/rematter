# Validate Command

Schema-based frontmatter validation for markdown files. Uses the standard `_run()` dispatcher (not a custom runner like sync).

## Schema Format

Schema lives at `<directory>/_schema.yml` by default, overridable with `--schema`.

```yaml
allow_extra: false  # optional, defaults to false (strict)

properties:
  created:
    type: timestamp
    required: true
    default: "%Y-%m-%d %H:%M"  # strftime format → stamped with current time on --fix
  publish:
    type: bool
    required: true
    default: false
  status:
    type: string
    required: false
    enum: [not_started, in_progress, on_hold, done, cancelled]
    default: not_started
  creators:
    type: list
    required: false
```

### Property Spec Fields

| Field | Purpose |
| --- | --- |
| `type` | One of: `timestamp`, `bool`, `string`, `list`, `int`, `float` |
| `required` | Key must exist in frontmatter (null values are valid) |
| `default` | Value to set on `--fix` if missing. Timestamp defaults with `%` are expanded via `strftime` |
| `enum` | Allowed values (string fields) |

### Semantics

- `required: true` means the key must exist — null is a valid value (e.g. `synced: null` before first sync)
- `allow_extra: false` (default) rejects any frontmatter key not declared in `properties`
- Validation is two-phase: structural (missing/unrecognized) → value-level (type, enum). Structural errors bail early.

## CLI

```bash
rematter validate <directory> [--schema PATH] [--fix] [--recursive] [--dry-run]
```

- Default mode: report-only, exit 1 if any files fail
- `--fix`: set defaults for missing properties that have a `default` defined
- `--fix` with required field missing and no default → still errors
- `--dry-run` + `--fix`: show what would change without writing

## Implementation

Key functions in `_workers.py`:

- `_load_schema(path)` — reads YAML, raises `FileNotFoundError` if missing
- `_validate_against_schema(fm, schema)` — pure validation, returns error list
- `_resolve_default(spec)` — expands strftime formats for timestamp defaults
- `_validate_worker(path, *, schema, fix, dry_run)` — per-file worker following standard `Result` pattern

Type checking uses `_SCHEMA_TYPE_CHECKERS` dict mapping type names to lambdas. The `timestamp` checker reuses `_is_timestamp_like()` from the sync pipeline.

## Planned Enhancements

- `nullable: false` schema option for strict non-null enforcement
- Type-tag conditional validation (different required fields per type tag)
- Config file support for schema path conventions (`.rematter/<name>.schema.yml`)
