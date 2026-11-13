# Skills Commands Reference

## skills install

```bash
koh skills install --agent
koh skills install [directory] --agent
koh skills install [directory] [--force] --agent
```

| Option        | Notes                                                                                                 |
| ------------- | ----------------------------------------------------------------------------------------------------- |
| `[directory]` | Target base directory; installs into `<directory>/skills/`. Defaults to `.agents/skills` in CWD.      |
| `[--force]`   | Removes existing bundled skill directories before installing; unrelated skill dirs are left unchanged |

Returns:

```ts
{
  data: {
    directory: string;
    installed: string[];
    skipped: string[];
  }
}
```
