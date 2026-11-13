# Environment Commands Reference

All environment commands (`list`, `show`, `create`, `update`, `remove`, and every `kv` subcommand) support both `--scope project` and `--scope workspace`. `--scope folder` throws `Not implemented`.

## Environment Types and Priority

Insomnia resolves variables across three hierarchical levels:

1. **Project Environments** – accessible across all workspaces in a project
2. **Workspace Environments** – accessible to all requests within a workspace
3. **Folder Environments** – accessible to requests within a specific folder

Each project and workspace environment has a **base environment** plus optional **sub-environments** (e.g. production, staging, development). Sub-environments inherit all variables from their parent and override values for specific scenarios. Sub-environments can also be marked **private**, in which case they are unsynced, unexported, and encrypted.

When the same variable is defined at multiple levels, Insomnia resolves the value using this precedence order (first match wins):

1. Folder environment
2. Selected workspace sub-environment
3. Workspace base environment
4. Selected project sub-environment
5. Project base environment

Secret variables are not supported in Koh yet.

By default — no `--project-environment` or `--workspace-environment` given — `koh request run` renders templates using only the request's workspace's own base environment; no project environment is applied. `--workspace-environment <id|name>` selects a specific workspace sub-environment (or re-selects the base) to use instead of the plain default base. `--project-environment <id|name>` opts a project environment or sub-environment into the merge; without it, no project variables are applied at all. Merge precedence, low to high: project base < selected project sub-environment < workspace base < selected workspace sub-environment. Koh then renders `{{ variable }}` templates once before sending the request. Folder environments and secrets are not resolved by Koh yet.

## Entity Schema

```ts
interface SubEnvironment {
  id?: string; // Format: env_<hex>
  name: string;
  created?: number;
  modified?: number;
  isPrivate?: boolean;
  data?: Record<string, unknown>;
}

interface ProjectEnvironment {
  id: string; // Format: env_<hex>
  name: string;
  filePath?: string;
  created?: number;
  modified?: number;
  data?: Record<string, unknown>;
  subEnvironments?: SubEnvironment[];
}

interface WorkspaceEnvironment {
  id: string; // Format: env_<hex>
  parentId: string;
  name: string;
  data?: Record<string, unknown>;
  subEnvironments?: SubEnvironment[];
}
```

## environment list

```bash
koh environment list --scope project --project <path> --agent
koh environment list --scope workspace --project <path> --agent
koh environment list [--query <text>] --scope project --project <path> --agent
koh environment list --parent <id|name> --scope project --project <path> --agent   # list sub-environments
koh environment list --parent <id|name> --scope workspace --project <path> --agent # list sub-environments
```

| Option                                 | Notes                                                                                                                         |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `[--query <text>]`                     | Case-insensitive match against `name`                                                                                         |
| `[--parent <id\|name>]`                | Parent environment; when given, lists its sub-environments instead. Supported with `--scope project` and `--scope workspace`. |
| `[--workspace <id\|name>]`             | Only list environments belonging to this workspace (`--scope workspace` only)                                                 |
| `--scope <project\|folder\|workspace>` | Defaults to `workspace`. `project` and `workspace` are implemented; `folder` throws `Not implemented`.                        |

Returns:

```ts
{
  data: (ProjectEnvironment | SubEnvironment | WorkspaceEnvironment)[];
}
```

## environment show

```bash
koh environment show <id|name> --scope project --project <path> --agent
koh environment show <id|name> --scope workspace [--workspace <id|name>] --project <path> --agent
koh environment show <id|name> --parent <id|name> --scope project --project <path> --agent   # show a sub-environment
koh environment show <id|name> --parent <id|name> --scope workspace --project <path> --agent # show a sub-environment
```

`--parent` is supported with `--scope project` and `--scope workspace`. `--workspace` optionally narrows the search to a specific workspace when `--scope workspace` and `idOrName` is ambiguous by name.

Returns:

```ts
{
  data: ProjectEnvironment | SubEnvironment | WorkspaceEnvironment;
}
```

## environment create

```bash
koh environment create --name <name> --scope project --project <path> --agent
koh environment create --name <name> --scope workspace --workspace <id|name> [--color <color>] --project <path> --agent
# Create a sub-environment within a parent environment (either scope)
koh environment create --name <name> --parent <id|name> --scope project --project <path> --agent
koh environment create --name <name> --parent <id|name> --scope workspace [--color <color>] --project <path> --agent
```

| Option                     | Notes                                                                                                  |
| -------------------------- | ------------------------------------------------------------------------------------------------------ |
| `[--color <color>]`        | Sub-environment color, or the environment's own color when `--scope workspace`                         |
| `[--parent <id\|name>]`    | Parent environment to create a sub-environment within                                                  |
| `[--workspace <id\|name>]` | Workspace to create the environment in. Required for `--scope workspace` when `--parent` is not given. |

Returns:

```ts
{
  data: ProjectEnvironment | WorkspaceEnvironment | SubEnvironment;
}
```

## environment update

```bash
koh environment update <id|name> [--name <name>] --scope project --project <path> --agent
koh environment update <id|name> [--name <name>] [--color <color>] --scope workspace [--workspace <id|name>] --project <path> --agent
# Update a sub-environment (either scope)
koh environment update <id|name> --parent <id|name> [--name <name>] --scope project --project <path> --agent
koh environment update <id|name> --parent <id|name> [--name <name>] [--color <color>] --scope workspace --project <path> --agent
```

At least one of `--name` or `--color` is required. `--workspace` optionally narrows the search to a specific workspace when `--scope workspace` and `idOrName` is ambiguous by name.

Returns:

```ts
{
  data: ProjectEnvironment | WorkspaceEnvironment | SubEnvironment;
}
```

## environment remove

```bash
koh environment remove <id|name> --scope project --project <path> --agent
koh environment remove <id|name> --scope workspace [--workspace <id|name>] --project <path> --agent
koh environment remove <id|name> --parent <id|name> --scope project --project <path> --agent   # remove a sub-environment
koh environment remove <id|name> --parent <id|name> --scope workspace --project <path> --agent # remove a sub-environment
```

**Warning**: Permanently deletes the environment (or sub-environment).

Returns:

```ts
{
  data: {
    removed: true;
    id: string;
    name: string;
  }
}
```

All `kv` subcommands accept `--scope project` or `--scope workspace`, plus `[--workspace <id|name>]` to narrow the search when `--scope workspace` and `idOrName` is ambiguous by name.

## environment kv list

```bash
koh environment kv list <id|name> --scope project --project <path> --agent
koh environment kv list <id|name> --scope workspace [--workspace <id|name>] --project <path> --agent
koh environment kv list <id|name> --parent <id|name> --scope project --project <path> --agent   # list a sub-environment's values
koh environment kv list <id|name> --parent <id|name> --scope workspace --project <path> --agent # list a sub-environment's values
```

Returns:

```ts
{
  data: Array<{
    key: string;
    value: unknown;
  }>;
}
```

## environment kv show

```bash
koh environment kv show <id|name> <key> --scope project --project <path> --agent
koh environment kv show <id|name> <key> --scope workspace [--workspace <id|name>] --project <path> --agent
koh environment kv show <id|name> <key> --parent <id|name> --scope project --project <path> --agent   # show a sub-environment's value
koh environment kv show <id|name> <key> --parent <id|name> --scope workspace --project <path> --agent # show a sub-environment's value
```

Returns:

```ts
{
  data: {
    key: string;
    value: unknown;
  }
}
```

## environment kv create / kv update

```bash
koh environment kv create <id|name> <key> <value> --scope project --project <path> --agent
koh environment kv create <id|name> <key> <value> --scope workspace [--workspace <id|name>] --project <path> --agent
koh environment kv create <id|name> <key> <value> --parent <id|name> --scope project --project <path> --agent   # create in a sub-environment
koh environment kv create <id|name> <key> <value> --parent <id|name> --scope workspace --project <path> --agent # create in a sub-environment
koh environment kv update <id|name> <key> <value> --scope project --project <path> --agent
koh environment kv update <id|name> <key> <value> --scope workspace [--workspace <id|name>] --project <path> --agent
koh environment kv update <id|name> <key> <value> --parent <id|name> --scope project --project <path> --agent   # update in a sub-environment
koh environment kv update <id|name> <key> <value> --parent <id|name> --scope workspace --project <path> --agent # update in a sub-environment
```

Upserts a top-level key on an environment or, with `--parent`, a sub-environment. `<value>` is parsed as JSON, e.g. `'"a string"'`, `'42'`, `'{"nested":true}'`.

Returns:

```ts
{
  data: {
    key: string;
    value: unknown;
  }
}
```

## environment kv remove

```bash
koh environment kv remove <id|name> <key> --scope project --project <path> --agent
koh environment kv remove <id|name> <key> --scope workspace [--workspace <id|name>] --project <path> --agent
koh environment kv remove <id|name> <key> --parent <id|name> --scope project --project <path> --agent   # remove from a sub-environment
koh environment kv remove <id|name> <key> --parent <id|name> --scope workspace --project <path> --agent # remove from a sub-environment
```

Removes a key from an environment or, with `--parent`, a sub-environment. `<key>` accepts either a plain top-level key or a JSON-path (e.g. `nested.field`) for nested values. Throws if the key is not found.

Returns:

```ts
{
  data: {
    key: string;
    removed: true;
  }
}
```
