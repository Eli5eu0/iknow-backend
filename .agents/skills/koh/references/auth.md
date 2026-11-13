# Auth

Grant-specific OAuth2 runtime flows. Configure the shared OAuth2 request auth shape in
[Requests](requests.md#oauth2-request-auth-configuration). Runtime behavior depends on the request's
OAuth2 `grantType`.

## Runtime support

| Grant type           | Runtime status                        | Notes                                                   |
| -------------------- | ------------------------------------- | ------------------------------------------------------- |
| `authorization_code` | Fetches and caches live access tokens | Interactive flow; uses `request run` or `auth begin`    |
| `client_credentials` | Fetches and caches live access tokens | Non-interactive flow; handled entirely by `request run` |
| `password`           | Fetches and caches live access tokens | Non-interactive flow; handled entirely by `request run` |
| `implicit`           | Fetches and caches live access tokens | Interactive flow; uses `request run` or `auth begin`    |

Unsupported grant types fail at runtime instead of starting an OAuth2 flow.

## `client_credentials` grant

OAuth2 `client_credentials` is non-interactive. `request run` handles the whole flow: it reuses a
valid cached token for the request, or POSTs `grant_type=client_credentials` to `accessTokenUrl` to
fetch a new one. The resulting access token is cached per request and sent on the API request as
`Authorization: <tokenPrefix> <access_token>` (`Bearer` by default).

Configure the request with `type: oauth2` and `grantType: client_credentials`. `accessTokenUrl` and
`clientId` are required at runtime; `clientSecret`, `scope`, `audience`, `resource`,
`credentialsInBody`, and `tokenPrefix` are optional. By default, client credentials are sent to the
token endpoint with HTTP Basic auth. Set `credentialsInBody=true` to send `client_id` and
`client_secret` in the form body instead.

For a `request create --auth` example, see
[Requests](requests.md#oauth2-request-auth-configuration). Run the configured request with:

```bash
koh request run "Service API" --workspace <id|name> --project <path> --agent
```

`client_credentials` does not use `auth begin` or `auth complete`, and it does not return
`interactive_auth_required`. If the token endpoint response includes `expires_in`, `koh` reuses the
cached token until it expires; when it expires, the next `request run` fetches a fresh token.

## `password` grant

OAuth2 `password` is non-interactive. `request run` handles the whole flow: it reuses a valid cached
token for the request, tries a refresh token when one is available, or POSTs `grant_type=password`
with `username` and `password` to `accessTokenUrl` to fetch a new one. The resulting access token is
cached per request and sent on the API request as
`Authorization: <tokenPrefix> <access_token>` (`Bearer` by default).

Configure the request with `type: oauth2` and `grantType: password`. `accessTokenUrl`, `clientId`,
`username`, and `password` are required at runtime; `clientSecret`, `scope`, `audience`,
`refreshToken`, `credentialsInBody`, and `tokenPrefix` are optional. By default, client credentials
are sent to the token endpoint with HTTP Basic auth. Set `credentialsInBody=true` to send
`client_id` and `client_secret` in the form body instead.

For a `request create --auth` example, see
[Requests](requests.md#oauth2-request-auth-configuration). Run the configured request with:

```bash
koh request run "Password Grant API" --workspace <id|name> --project <path> --agent
```

`password` does not use `auth begin` or `auth complete`, and it does not return
`interactive_auth_required`. If the token endpoint response includes `expires_in`, `koh` reuses the
cached token until it expires; when it expires, the next `request run` refreshes the token when
possible or fetches a fresh password-grant token.

## `implicit` grant

OAuth2 `implicit` is interactive. The provider returns the token directly in the authorize
redirect's URL **fragment** (`#access_token=...`) — there is no token endpoint, no `clientSecret`,
and no PKCE. `request run` starts the flow the same way as `authorization_code`: with no cached
token it returns `errorCode: 'interactive_auth_required'` with `errorData.authorizeUrl` +
`errorData.sessionId`, and opens the browser. See [request run needs auth](#request-run-needs-auth).

Configure the request with `type: oauth2` and `grantType: implicit`. `authorizationUrl` and
`clientId` are required at runtime; `responseType` (default `token`; one of `token`, `id_token`,
`id_token token`), `redirectUrl`, `scope`, `state`, `audience`, and `tokenPrefix` are optional. When
`responseType` includes `id_token`, `koh` adds a generated `nonce` to the authorize URL.

The fragment carries an `access_token` (`response_type=token` / `id_token token`) and/or an
`id_token` (`response_type=id_token` / `id_token token`). The request is sent with the access token
when present, falling back to the id token for the `response_type=id_token` case (no access token).
`errorData.grantType` on the needs-auth response is `implicit`.

Because the token arrives in the fragment (not a query code), resume with `--redirect-url` and paste
the browser's **final** URL — `--code` does not apply to implicit:

```bash
koh auth complete --session <sessionId> --redirect-url "<final URL with #access_token=... or #id_token=...>" --agent
```

Implicit tokens have no refresh token. `koh` reuses the cached token until `expires_in` elapses;
after that, the next `request run` restarts the interactive flow.

## `authorization_code` grant

`request run` usually starts this flow for you and returns a response with `errorData.sessionId` +
`errorData.resumeCommand` when a request has no cached token yet. `auth begin` is only for pre-authenticating a request before you
run it. `koh` never reads stdin and never blocks — `auth complete` takes the code as an argument, so
it works the same whether a human runs it directly or an agent runs it after prompting its human in
chat.

### request run needs auth

If a request uses OAuth2 `authorization_code` auth and has no cached token, `request run` returns an
error response with the normal response artifact fields plus structured auth data:

```ts
{
  data: {
    statusCode: 0;
    statusMessage: 'Error';
    errorCode: 'interactive_auth_required';
    errorData: {
      authorizeUrl: string; // open this if the browser didn't
      sessionId: string; // pass to `auth complete`
      grantType: 'authorization_code' | 'implicit'; // implicit resumes with --redirect-url only
      resumeCommand: string; // a copyable `auth complete` command template with placeholders
    }
    bodyPath: string;
    timelinePath: string;
  }
}
```

Show `data.errorData.authorizeUrl` to your human, get the code (or the full redirect URL) back, then run
`auth complete` with the returned `data.errorData.sessionId`. After that, re-run the original
`request run` — the token is cached and the request can complete normally.

### auth complete

```bash
koh auth complete --session <sessionId> --code <code> --agent
koh auth complete --session <sessionId> --redirect-url <url> --agent
```

Exchanges an `authorization_code` code for a token and caches it, keyed by the request the session
was started for. Resumes a `sessionId` from a `request run` response's `errorData` or from `auth begin`.

| Option                 | Notes                                                                              |
| ---------------------- | ---------------------------------------------------------------------------------- |
| `--session <id>`       | Required. From `request run`'s needs-auth result or `auth begin`                   |
| `--code <code>`        | The bare authorization code returned by the provider                               |
| `--redirect-url <url>` | The full redirect URL returned by the provider (contains the code); parsed for you |

Provide exactly one of `--code` / `--redirect-url`. The session has a short TTL (~10 minutes) —
an unknown or expired session errors; re-run `request run` (or `auth begin`) to get a fresh one.

Returns a token summary — never the raw token (it stays in the per-user cache):

```ts
{
  data: {
    cached: true;
    expiresAt: number | null; // ms epoch, or null if the provider didn't send expires_in
    hasRefreshToken: boolean;
  }
}
```

After this, re-run the original `request run` — it now reads the cached token automatically.

### auth token clear

```bash
koh auth token clear <requestId> --agent
```

Deletes the cached OAuth2 token for a request id, for example when the provider-side token was
disabled or revoked. The next interactive OAuth2 `request run` returns `interactive_auth_required`;
non-interactive grants fetch a fresh token.

The cache key is the request id, not the request name. This command does not accept `--workspace`,
does not require `--project` or `--app-data`, and only removes koh's local cache entry under
`KOH_DATA_DIR/oAuth2` or `~/.koh/oAuth2`. It does not edit request auth, clear pending sessions,
clear all tokens, or revoke provider-side tokens.

Returns an idempotent result and never prints token values:

```ts
{
  data: {
    cleared: boolean; // true when a cached token existed and was removed
    requestId: string;
  }
}
```

### auth begin

```bash
koh auth begin <id|name> [--workspace <id|name>] --project <path> --agent
```

Starts the interactive flow for a request without running it (pre-authenticate ahead of time). The
request's auth must be `type: oauth2` with `grantType: authorization_code` or `implicit`. For
`implicit`, resume with `auth complete --redirect-url` (the token is in the URL fragment).

| Option                     | Notes                                      |
| -------------------------- | ------------------------------------------ |
| `<id\|name>`               | Request id or request name                 |
| `[--workspace <id\|name>]` | Scope request lookup to a single workspace |

Returns:

```ts
{
  data: {
    authorizeUrl: string;
    sessionId: string;
  }
}
```

Show `authorizeUrl` to your human, then call `auth complete` with the code they get back.
