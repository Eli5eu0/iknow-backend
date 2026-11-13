---
name: koh
description: >
  Manages Insomnia API collections, documents, requests, cookies, and project environments via the cli command — lists, shows, searches, creates, updates, runs, validates, and removes resources in an Insomnia project.
  Use when the user is working with Insomnia projects, HTTP requests, or OpenAPI specs.
compatibility: Requires koh-cli and Node.js >= 22.19.0.
metadata:
  version: 0.4.1
allowed-tools: Bash(koh:*) Bash(npx koh-cli:*)
---

# Koh CLI Skill

**Installation**:
If the CLI is not globally available (`npm install -g koh-cli`), use `npx koh-cli` as a fallback.

## 1. Version Check & Self-Healing (CRITICAL FIRST STEP)

Before executing any Koh workflow, run `koh --version` and compare it to `metadata.version` in this skill's frontmatter.

- **If CLI version < Skill version (CLI is outdated)**: Do NOT reinstall skills. You must use the specified CLI version.
- **If CLI version > Skill version (Skill is outdated)**: Your documentation is stale and must be refreshed. Run `koh skills install ~/.agents --force` (replace `~/.agents` with your actual agent storage path; `--force` ensures all existing skill files are replaced).

## 2. Environment & Context

The CLI currently only supports git projects. For non-git projects, please wait for a future cli update.

**Git Project Detection**:
An Insomnia v5 Git project is a local directory containing one or more `.yaml` files whose first line contains `insomnia.rest`.
Passing a non-project directory will silently return empty results. If output is unexpectedly empty, inspect the target directory and the first line of its YAML files before assuming the project has no resources.

## 3. Domain Model (Core Concepts)

Before executing commands, understand the hierarchy of Insomnia entities:

- **Project**: The top-level local OS directory containing the `.yaml` files.
- **Workspace**: A logical grouping of Collections and Documents within a Project. Workspace is a conceptual grouping, not usually a command argument.
  - **Collection**: The top-level API definitions within a Project.
  - **Document**: A superset of Collection that includes an open API spec.
- **Folder**: An optional grouping container used to organize Requests.
- **Request**: A specific HTTP request definition.

**Hierarchy rules**:

```
Project
├── Collection|Document
│   ├── Folder (optional)
│   │   └── Request
│   └── Request (if no Folder)
```

## 4. Agent Operating Rules (Gotchas & Workflows)

You MUST follow these rules when operating the CLI:

1. **Mandatory JSON Output**: ALWAYS append `--agent` to your commands. This guarantees structured JSON output (e.g., `{"data": [], "hints": []}` or `{"error": "Error message", "hints": []}`) instead of human-readable text.
2. **Explicit Target Directory**: ALWAYS scope commands with `--project <directory_path>` unless you have explicitly verified that your current working directory is the Insomnia v5 project root.
3. **ID over Name (Identifier Resolution)**: Commands accept either `<id>` or `<name>`.
   - Exact ID matches are prioritized (e.g., `wrk_829522b5e8dc4f37b7529db150315cd4`).
   - If a name is ambiguous (2+ matches), the command will fail and list the matching IDs. You MUST rerun the command using the exact ID.
4. **Destructive Actions are Permanent**: There is no soft-delete or undo. ALWAYS resolve names to IDs and confirm the target before running `remove` commands.

## 5. Command Router

Use the overview below to find the correct command syntax. If you need full flags, advanced options, or examples, read the corresponding `references/*.md` file.

**Global Options**:

- `--project <value>`: YAML mode: path to the Project directory (defaults to current directory); app-data mode: project id/name.
- `--app-data [path]`: Switch to Insomnia app-data mode. Optionally provide the data directory; defaults to the system default. See [App-Data Mode](references/app-data.md) for full details.
- `--agent`: Output structured JSON for Agent/LLM consumption.

### Collections

```bash
koh collection list [--query <text>] --project <path> --agent
koh collection show <id|name> --project <path> --agent
koh collection create --name "..." [--description "..."] --project <path> --agent
koh collection update <id|name> [--name "..."] [--description "..."] --project <path> --agent
koh collection remove <id|name> --project <path> --agent
```

See [Collections](references/collections.md) for full details.

### Requests

```bash
koh request list [--workspace <id|name>] [--query <text>] --project <path> --agent
koh request show <id|name> [--workspace <id|name>] --project <path> --agent
koh request create --name "..." [--workspace <id|name>] [--parent <id>] [--setting-send-cookies <boolean>] [--setting-store-cookies <boolean>] --project <path> --agent
koh request update <id|name> [--workspace <id|name>] [--setting-send-cookies <boolean>] [--setting-store-cookies <boolean>] --project <path> --agent
koh request run <id|name> [--workspace <id|name>] [--project-environment <id|name>] [--workspace-environment <id|name>] [--url <url>] [--method <method>] [-H <header...>] [-p <param...>] [--body <body>] [--file-body <path>] [--mime <type>] [--auth <auth>] [--body-output auto|file] [--max-body-bytes <bytes>] [--data-folder <folder...>] --project <path> --agent
koh request remove <id|name> [--workspace <id|name>] --project <path> --agent
```

See [Requests](references/requests.md) for full details.

### Auth

For OAuth2 `authorization_code` and `implicit`, `request run` returns a response with
`errorData.sessionId` when a request has no cached token yet — usually you don't call `auth begin`
directly. `implicit` returns its token in the redirect fragment, so resume it with
`auth complete --redirect-url` (not `--code`). OAuth2 `client_credentials` and `password` fetch
tokens non-interactively during `request run`. OAuth 1.0 is stateless and needs no such flow:
`request run` signs each request locally (see [Requests](references/requests.md)).

```bash
koh auth complete --session <sessionId> --code <code> --agent
koh auth complete --session <sessionId> --redirect-url <url> --agent
koh auth begin <id|name> [--workspace <id|name>] --project <path> --agent
koh auth token clear <requestId> --agent
```

See [Auth](references/auth.md) for full details.

### Cookies

Every `cookie` command needs `--workspace <id|name>` (a collection or a document), and targets a cookie by `id` or `key`. `request run` uses this jar: requests with `--setting-send-cookies` attach matching cookies, and `--setting-store-cookies` saves response `Set-Cookie`s back into it.

`--workspace <id|name>` is shown below as `<scope>`.

```bash
koh cookie list <scope> [--query <text>] --project <path> --agent
koh cookie show <id|key> <scope> [--domain <domain>] --project <path> --agent
koh cookie create <scope> --key "..." --value "..." --domain "..." [options] --project <path> --agent
koh cookie update <id|key> <scope> [--match-domain <domain>] [options] --project <path> --agent
koh cookie remove <id|key> <scope> [--domain <domain>] --project <path> --agent
koh cookie clear <scope> --project <path> --agent
```

See [Cookies](references/cookies.md) for full details.

### Documents

```bash
koh document list --project <path> --agent
koh document show <id|name> --project <path> --agent
koh document remove <id|name> --project <path> --agent
```

See [Documents](references/documents.md) for full details.

### Document Spec

```bash
koh document spec show --document <id|name> --project <path> --agent
```

See [Document Spec](references/document_spec.md) for full parameter documentation.

### Document Spec Operation

```bash
koh document spec operation list --document <id|name> --project <path> --agent
koh document spec operation search --document <id|name> [--query <text>] [--filter-json <json>] --project <path> --agent
koh document spec operation show --document <id|name> --operation-id <operationId> --project <path> --agent
```

See [Document Spec Operation](references/document_spec_operation.md) for full parameter documentation.

### Imports

```bash
# `import oas` accepts OpenAPI 3.x AND Swagger 2.0 (Swagger 2.0 is OpenAPI 2.0)
# Import an OpenAPI/Swagger Spec as or into a Collection
koh import oas collection <file_path> [--target <id|name>] --project <path> --agent
# Import an OpenAPI/Swagger Spec as or into a Document
koh import oas document <file_path> [--target <id|name>] --project <path> --agent
# Import a cURL command as a request (from a file, stdin, or an inline string)
koh import curl --from-file <path> --workspace <id|name> [--name <name>] --project <path> --agent
koh import curl - --workspace <id|name> [--name <name>] --project <path> --agent   # read from stdin
```

See [Import](references/import.md) for full details.

### Environments

`list`, `show`, `create`, `update`, `remove`, and all `kv` commands support both `--scope project` and `--scope workspace` (`--scope folder` throws `Not implemented`).

```bash
koh environment list [--query <text>] --scope project --project <path> --agent
koh environment list [--query <text>] --scope workspace --project <path> --agent
koh environment show <id|name> --scope project --project <path> --agent
koh environment show <id|name> --scope workspace --project <path> --agent
koh environment create --name "..." [--description "..."] --scope project --project <path> --agent
koh environment create --name "..." --scope workspace --workspace <id|name> [--color "..."] --project <path> --agent
koh environment update <id|name> [--name "..."] [--description "..."] --scope project --project <path> --agent
koh environment update <id|name> [--name "..."] [--color "..."] --scope workspace --project <path> --agent
koh environment remove <id|name> --scope project --project <path> --agent
koh environment remove <id|name> --scope workspace --project <path> --agent

# Sub-environments: pass --parent <id|name> to target the parent environment (either scope)
koh environment list --parent <id|name> --scope project --project <path> --agent
koh environment create --name "..." --parent <id|name> --scope project --project <path> --agent
koh environment create --name "..." --parent <id|name> --scope workspace --project <path> --agent
```

See [Environments](references/environments.md) for full details.

### Exports

```bash
# Export a request as a cURL command
koh export request <id|name> [--workspace <id|name>] --project <path> --agent
```

See [Export](references/export.md) for full details.

### Validate

```bash
koh validate <file_or_directory...> [--agent]
```

Validates YAML files against the public v5.1 JSON schema. Exits `1` when any file is invalid. Takes explicit paths and ignores `--project`.

See [Validate](references/validate.md) for output shapes and schema limitations.
