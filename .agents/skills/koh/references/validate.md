# Validate Command Reference

Validates Insomnia YAML files against the **public v5.1 JSON schema**, fetched at runtime from `https://raw.githubusercontent.com/Kong/insomnia/develop/schemas/insomnia.schema.5.1.json` (network access required; a fetch failure aborts with an error).

## validate

```bash
koh validate <files...> [--agent]
koh validate <directory...> [--agent]   # directories expand to their immediate .yaml/.yml files (non-recursive)
```

Exit codes:

- `0` — every file is valid
- `1` — at least one file is invalid **or** the schema fetch failed

## Agent output

Valid files only:

```json
{
  "data": {
    "files": [{ "path": "<abs path>", "valid": true, "errors": [] }]
  }
}
```

Invalid files add the `invalid` count:

```json
{
  "data": {
    "files": [{ "path": "<abs path>", "valid": false, "errors": ["/meta: must have required property 'id'"] }],
    "invalid": 1
  }
}
```

Schema fetch failure:

```json
{ "error": "Failed to fetch schema (404 Not Found) from https://..." }
```

## Gotchas

- **Loose nested schema**: nested nodes (requests/folders inside `collection:`) are validated against an `anyOf` whose branches accept most shapes. A request missing `method` or with wrong-typed properties can pass as a folder/websocket node. Catchable nested violations are limited — e.g. `meta` present without `id` (`/collection/0/meta: must have required property 'id'`). Do not treat `validate` as proof of deep request semantics.
- **Cross-branch noise**: because every `anyOf` branch is tried, error lists can include messages from unrelated branches (e.g. `must have required property 'reflectionApi'` for a non-gRPC node). Identical duplicate messages are deduplicated.
- **Non-existent files** are reported as invalid with an `ENOENT` error rather than aborting the run.
