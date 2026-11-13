# App-Data Mode Reference

## Overview

Pass `--app-data` to read from the Insomnia desktop app's local database instead of a v5 YAML Git project.

```bash
koh --app-data [path] --project <id|name> <command> --agent
```

## `--app-data [path]`

| Value                     | Behaviour                                    |
| ------------------------- | -------------------------------------------- |
| Absent                    | YAML mode (default, unchanged)               |
| `--app-data` (no value)   | App-data mode, system default data directory |
| `--app-data /custom/path` | App-data mode, custom data directory         |

**System default data directories**:

| Platform | Default path                                        |
| -------- | --------------------------------------------------- |
| macOS    | `~/Library/Application Support/Insomnia`            |
| Windows  | `%APPDATA%\Insomnia`                                |
| Linux    | `~/.config/Insomnia` (or `$XDG_DATA_HOME/Insomnia`) |

The environment variable `INSOMNIA_DATA_PATH` overrides the system default on all platforms.

## `--project` in app-data mode

In app-data mode `--project` selects a project by **id or name** (not a directory path).

| `--project` | TTY / `--agent`                           | Behaviour                                              |
| ----------- | ----------------------------------------- | ------------------------------------------------------ |
| Provided    | any                                       | Resolve by id or name; error if not found              |
| Absent      | TTY available, no `--agent`               | Interactive numbered picker                            |
| Absent      | No TTY (stdin or stdout) **or** `--agent` | Error: `--project is required in non-interactive mode` |

## Examples

```bash
# App-data mode with explicit project id
koh --app-data --project proj_abc123 collection list --agent

# App-data mode with project name
koh --app-data --project "My API" collection list --agent

# Custom data directory
koh --app-data ~/backups/Insomnia --project proj_abc123 collection list --agent
```

## Notes

- Without a TTY (or when using `--agent`), interactive project selection is disabled; you must provide `--project`.
- Write commands (`create`, `update`, `remove`, etc.) share the same NeDB files as the Insomnia app. Running both concurrently risks conflicting or corrupting data. Read-only commands (`list`, `show`) carry no such risk. If the app may be open, decide how to proceed — e.g. warn the user, ask them to close it, or abort the write.
