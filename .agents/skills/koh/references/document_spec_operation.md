# Document Spec Operation Commands Reference

## Entity Schema

```ts
interface OperationSummary {
  method: string;
  path: string;
  operationId?: string;
  summary?: string;
  tags: string[];
}

// SpecOperation fields merged with the full OpenAPI operation object (all $refs resolved inline)
interface OperationDetail {
  method: string;
  path: string;
  operationId?: string;
  summary?: string;
  description?: string;
  tags: string[];
  parameters?: object[];
  requestBody?: object;
  responses?: object;
  callbacks?: object;
  deprecated?: boolean;
  security?: object[];
  servers?: object[];
}

interface SpecFilter {
  method?: string; // Normalized to uppercase before comparison
  path?: string; // Exact match by default (see `match`)
  operationId?: string;
  tag?: string; // Matches if operation includes this tag
  summary?: string; // Case-insensitive substring
  description?: string; // Case-insensitive substring
  text?: string; // Case-insensitive substring across method, path, operationId, summary, description, tags
  all?: SpecFilter[]; // Every child must match
  any?: SpecFilter[]; // At least one child must match
  not?: SpecFilter; // Operation must not match
  match?: 'exact' | 'normalized'; // Root-only; 'normalized' ignores query strings, fragments, duplicate/trailing slashes
  limit?: number; // Root-only; max results to return
}
```

## document spec operation list

```bash
koh document spec operation list --document <id|name> --project <path> --agent
```

Returns:

```ts
{
  data: {
    results: OperationSummary[];
  }
}
```

## document spec operation search

```bash
koh document spec operation search --document <id|name> [--query <text>] [--filter-json <json>] --project <path> --agent
```

| Option                 | Notes                                                                                   |
| ---------------------- | --------------------------------------------------------------------------------------- |
| `--query <text>`       | Case-insensitive query across method, path, operationId, summary, description, and tags |
| `--filter-json <json>` | `SpecFilter` object; leaf fields combined as implicit AND; unsupported fields rejected  |

At least one of `--query` or `--filter-json` is required. When both are provided, the query is combined with the structured filter as an implicit AND.

Returns:

```ts
{
  data: {
    results: OperationSummary[];
  }
}
```

## document spec operation show

```bash
koh document spec operation show --document <id|name> --operation-id <operationId> --project <path> --agent
```

Returns:

```ts
{
  data: OperationDetail; // flat merge of SpecOperation fields and OpenAPI operation fields
}
```
