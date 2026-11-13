# Document Spec Commands Reference

## Entity Schema

```ts
interface SpecDocument {
  openapi?: string;
  swagger?: string;
  info?: object;
  servers?: object[];
  tags?: object[];
  externalDocs?: object;
}
```

## document spec show

```bash
koh document spec show --document <id|name> --project <path> --agent
```

**Note**: Returns top-level spec fields only (`openapi` or `swagger`, `info`, `servers`, `tags`, `externalDocs`). Does not return the full spec content.

Returns:

```ts
{
  data: SpecDocument;
}
```
