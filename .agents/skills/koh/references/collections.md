# Collection Commands Reference

## Entity Schema

```ts
interface Collection {
  id: string; // Format: wrk_<uuid>
  name: string;
  description?: string;
  filePath?: string; // Present only for git-synced projects
  created?: number;
  modified?: number;
}
```

## collection list

```bash
koh collection list --project <path> --agent
koh collection list [--query <text>] --project <path> --agent
```

| Option             | Notes                                                  |
| ------------------ | ------------------------------------------------------ |
| `[--query <text>]` | Case-insensitive match across `name` and `description` |

Returns:

```ts
{
  data: Collection[];
}
```

## collection show

```bash
koh collection show <id|name> --project <path> --agent
```

Returns:

```ts
{
  data: Collection;
}
```

## collection create

```bash
koh collection create --name <name> [--description <desc>] [--file-path <path>] --project <path> --agent
```

| Option                 | Notes                                                            |
| ---------------------- | ---------------------------------------------------------------- |
| `[--file-path <path>]` | YAML filename relative to project dir; auto-generated if omitted |

Returns:

```ts
{
  data: Collection;
}
```

## collection update

```bash
koh collection update <id|name> [--name <name>] [--description <desc>] --project <path> --agent
```

Returns:

```ts
{
  data: Collection;
}
```

## collection remove

```bash
koh collection remove <id|name> --project <path> --agent
```

**Warning**: Permanently deletes the collection.

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
