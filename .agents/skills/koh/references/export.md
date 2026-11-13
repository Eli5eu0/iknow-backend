# Export Commands Reference

## export request

Export a request as a runnable cURL command.

```bash
koh export request <id|name> [--workspace <id|name>] --project <path> --agent
```

| Option            | Notes                                             |
| ----------------- | ------------------------------------------------- |
| `[--workspace …]` | Scope the request lookup to a specific workspace. |

Returns:

```ts
{
  data: string; // the cURL command
}
```
