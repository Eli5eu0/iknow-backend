# Import Commands Reference

`import oas` accepts both **OpenAPI 3.x** and **Swagger 2.0** (Swagger 2.0 is OpenAPI 2.0).

## import oas collection

```bash
koh import oas collection <file> --project <path> --agent
koh import oas collection <file> [--target <id|name>] --project <path> --agent
```

| Option                  | Notes                                                                                                                                                                                                                                |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `[--target <id\|name>]` | Without `--target`: creates new collection named after `info.title` (falls back to filename). With `--target`: looks up by ID or exact name and merges imported requests into it; creates new collection with that name if no match. |

Returns:

```ts
{
  data: {
    collection: {
      id: string;
      name: string;
    }
    imported: {
      folders: number;
      requests: number;
    }
  }
}
```

## import oas document

```bash
koh import oas document <file> --project <path> --agent
koh import oas document <file> [--target <id|name>] --project <path> --agent
```

| Option                  | Notes                                                                                                                                                                                                             |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `[--target <id\|name>]` | Without `--target`: creates new document named after `info.title` (falls back to filename). With `--target`: looks up by ID or exact name and replaces its spec; creates new document with that name if no match. |

Returns:

```ts
{
  data: {
    document: {
      id: string;
      name: string;
    }
    imported: {
      folders: number;
      requests: number;
    }
  }
}
```

## import curl

Import a cURL command as a request in an existing workspace (collection or document) or folder. Parsing is backed by [curlconverter](https://github.com/curlconverter/curlconverter), covering the common curl flag set (method, headers, body, basic/bearer auth).

```bash
koh import curl <curl> --workspace <id|name> [--name <name>] --project <path> --agent
koh import curl --from-file <path> --workspace <id|name> [--name <name>] --project <path> --agent
# Heredoc keeps a multi-line cURL command in a single tool call
koh import curl - --workspace <id|name> [--name <name>] --project <path> --agent << 'EOF'
curl <url>
EOF
```

| Option                   | Notes                                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------------ |
| `<curl>`                 | Inline cURL command, `-` to read from stdin, or omit and use `--from-file`. Provide exactly one. |
| `--from-file <path>`     | Read the cURL command from a file.                                                               |
| `--workspace <id\|name>` | Target workspace. One of `--workspace`/`--parent` is required.                                   |
| `[--parent <id>]`        | Workspace or folder ID; overrides `--workspace`.                                                 |
| `[--name <name>]`        | Defaults to `METHOD <url>`.                                                                      |

Scheme-less URLs follow curl's default of assuming `http://`.

Returns:

```ts
{
  data: {
    request: Request; // see requests.md
  }
}
```
