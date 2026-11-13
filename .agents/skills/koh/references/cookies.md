# Cookie Commands Reference

Cookies live in one **cookie jar** per workspace (collection or document). Every `cookie` command needs a scope — written `<scope>` below — which is `--workspace <id|name>`. `cookie create` creates the jar when none exists.

Cookies are addressed by `<id|key>`: an exact `id` (a UUID) or the cookie `key`. When several cookies share a key the command errors as ambiguous — disambiguate with `--domain` (`--match-domain` on `update`) or use the `id`.

The jar is also used at run time: a request with `--setting-send-cookies` attaches matching cookies to its outgoing `Cookie` header, and `--setting-store-cookies` writes the response's `Set-Cookie` cookies back into the jar (see [Requests](requests.md)). Domain/path/secure/expiry matching follows standard cookie rules.

## Entity Schema

```ts
// Mirrors Insomnia's cookie model; `cookie` commands return this shape (or arrays of it).
interface Cookie {
  id: string; // auto-generated UUID; not user-supplied
  key: string;
  value: string;
  domain: string;
  path: string;
  expires: string | number | null; // ISO string or epoch; never a Date on disk
  secure: boolean;
  httpOnly: boolean;
  hostOnly?: boolean;
}
```

## cookie list

```bash
koh cookie list <scope> [--url <url>] [--query <text>] --project <path> --agent
```

| Option             | Notes                                                                       |
| ------------------ | --------------------------------------------------------------------------- |
| `[--url <url>]`    | Only cookies that would be **sent to this URL** (domain/path/secure/expiry) |
| `[--query <text>]` | Case-insensitive match across `key`, `domain`, `value`                      |

Returns `{ data: Cookie[] }`.

## cookie show

```bash
koh cookie show <id|key> <scope> [--domain <domain>] --project <path> --agent
```

| Option                | Notes                                          |
| --------------------- | ---------------------------------------------- |
| `[--domain <domain>]` | Disambiguate when multiple cookies share a key |

Returns `{ data: Cookie }`.

## cookie create

```bash
koh cookie create <scope> --key <key> --value <value> --domain <domain> [options] --project <path> --agent
```

| Option                    | Notes                        |
| ------------------------- | ---------------------------- |
| `--key <key>`             | Cookie key (required)        |
| `--value <value>`         | Cookie value (required)      |
| `--domain <domain>`       | Cookie domain (required)     |
| `[--path <path>]`         | Cookie path (default `/`)    |
| `[--expires <expires>]`   | Expiry as an ISO date string |
| `[--secure <boolean>]`    | `true`/`false`               |
| `[--http-only <boolean>]` | `true`/`false`               |
| `[--host-only <boolean>]` | `true`/`false`               |

Returns `{ data: Cookie }`.

## cookie update

```bash
koh cookie update <id|key> <scope> [--match-domain <domain>] [fields] --project <path> --agent
```

At least one field flag is required. `--domain` here **sets** the cookie's domain; use `--match-domain` to pick the target when multiple cookies share a key.

| Option                      | Notes                                    |
| --------------------------- | ---------------------------------------- |
| `[--match-domain <domain>]` | Disambiguate the target cookie by domain |
| `[--key <key>]`             | New key                                  |
| `[--value <value>]`         | New value                                |
| `[--domain <domain>]`       | New domain                               |
| `[--path <path>]`           | New path                                 |
| `[--expires <expires>]`     | New expiry (ISO date string)             |
| `[--secure <boolean>]`      | `true`/`false`                           |
| `[--http-only <boolean>]`   | `true`/`false`                           |
| `[--host-only <boolean>]`   | `true`/`false`                           |

Returns `{ data: Cookie }`.

## cookie remove

```bash
koh cookie remove <id|key> <scope> [--domain <domain>] --project <path> --agent
```

**Warning**: Permanently removes the cookie from the jar.

| Option                | Notes                                          |
| --------------------- | ---------------------------------------------- |
| `[--domain <domain>]` | Disambiguate when multiple cookies share a key |

Returns `{ data: { removed: true; id: string; key: string; domain: string } }`.

## cookie clear

```bash
koh cookie clear <scope> --project <path> --agent
```

**Warning**: Permanently removes **all** cookies from the jar.

Returns `{ data: { cleared: true; count: number } }`.
