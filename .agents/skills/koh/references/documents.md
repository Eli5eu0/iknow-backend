# Document Commands Reference

## Entity Schema

```ts
interface Document {
  id: string; // Format: wrk_<uuid>
  name: string;
  description?: string;
  filePath?: string; // Present only for git-synced projects
  created?: number;
  modified?: number;
}
```

## document list

```bash
koh document list --project <path> --agent
```

Returns:

```ts
{ data: Document[] }
```

## document show

```bash
koh document show <id|name> --project <path> --agent
```

Returns:

```ts
{
  data: Document;
}
```

## document remove

```bash
koh document remove <id|name> --project <path> --agent
```

**Warning**: Permanently deletes the document.

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
