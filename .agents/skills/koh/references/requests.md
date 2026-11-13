# Request Commands Reference

## Entity Schema

```ts
interface RequestParameter {
  name: string;
  value: string;
  description?: string;
  disabled?: boolean;
  type?: string; // "text" | "file"
  multiline?: boolean | string;
}

interface RequestBodyParam extends RequestParameter {
  fileName?: string; // present for file fields
}

interface Request {
  id: string; // Format: req_<uuid>
  parentId: string; // Parent folder or workspace (collection or document) ID
  name: string;
  method: string;
  url: string;
  description?: string;
  headers?: Array<{ name: string; value: string; description?: string; disabled?: boolean }>;
  parameters?: Array<RequestParameter>;
  pathParameters?: Array<{ name: string; value: string }>;
  body?:
    | { mimeType: string; text?: string }
    | { mimeType: 'application/x-www-form-urlencoded'; params: Array<RequestParameter> }
    | { mimeType: 'multipart/form-data'; params: Array<RequestBodyParam> }
    | { mimeType: string; fileName: string }; // file upload body
  authentication?:
    | { type: 'none' }
    | { type: 'basic'; username: string; password: string; useISO88591?: boolean }
    | { type: 'bearer'; token: string; prefix?: string }
    | { type: 'digest'; username: string; password: string }
    | { type: 'apikey'; key: string; value: string; addTo: 'header' | 'query' }
    | OAuth1Config // see "OAuth1 request auth configuration" below
    | OAuth2Config; // see "OAuth2 request auth configuration" below
  disableUserAgentHeader?: boolean;
  settingSendCookies?: boolean;
  settingStoreCookies?: boolean;
  created?: number;
  modified?: number;
}

interface InteractiveAuthRequiredErrorData {
  authorizeUrl: string;
  sessionId: string;
  resumeCommand: string; // copyable `auth complete` command template with placeholders
}

type ResponseErrorFields =
  | { errorCode?: undefined; errorData?: undefined }
  | { errorCode: 'interactive_auth_required'; errorData: InteractiveAuthRequiredErrorData };

interface ResponseBase {
  statusCode: number;
  statusMessage: string;
  httpVersion: string;
  contentType: string;
  url: string;
  bytesRead: number;
  bytesContent: number;
  elapsedTime: number;
  headers: Array<{ name: string; value: string }>;
  bodyPath: string; // Actual bodies are stored on the filesystem
  timelinePath: string; // Actual timelines are stored on the filesystem
  bodyCompression?: Compression; // 'zip' | null
  body?: string; // Response body content, omitted when body is binary, exceeds --max-body-bytes, or mode is 'file'
  error?: string;
}

type Response = ResponseBase & ResponseErrorFields;
```

## OAuth1 request auth configuration

OAuth 1.0 is stateless: `request run` signs each request locally and appends an
`Authorization: OAuth ...` header. There is no token endpoint, browser flow, or cache — you supply
the consumer and token credentials directly. Fields match Insomnia desktop's OAuth 1.0 auth.

```ts
interface OAuth1Config {
  type: 'oauth1';
  disabled?: boolean;
  signatureMethod?: 'HMAC-SHA1' | 'HMAC-SHA256' | 'RSA-SHA1' | 'PLAINTEXT'; // default HMAC-SHA1
  consumerKey?: string;
  consumerSecret?: string;
  tokenKey?: string;
  tokenSecret?: string;
  privateKey?: string; // PEM, used only by RSA-SHA1
  version?: string; // default '1.0'
  nonce?: string; // blank → generated per request
  timestamp?: string; // blank → generated per request
  callback?: string;
  realm?: string;
  verifier?: string;
  includeBodyHash?: boolean; // adds oauth_body_hash for application/x-www-form-urlencoded bodies
}
```

Set it via `--auth "oauth1:key=value;key2=value2;..."` on `request create` / `request update` /
`request run`. `signatureMethod` defaults to `HMAC-SHA1` and `version` to `1.0`. `disabled` and
`includeBodyHash` are coerced to booleans; all other fields are strings. Unknown keys are rejected.
Multiline RSA private keys are impractical inline — configure `RSA-SHA1` requests via stored YAML.

```bash
koh request create --name "Legacy API" --workspace <id|name> \
  --auth "oauth1:consumerKey=ck;consumerSecret=cs;tokenKey=tk;tokenSecret=ts" \
  --project <path> --agent

koh request run "Legacy API" --workspace <id|name> --project <path> --agent
```

## OAuth2 request auth configuration

OAuth2 configuration is stored on a request via `authentication`. The `OAuth2Config` shape is the
shared storage contract for all OAuth2 grants, not a guarantee that every field applies to every
grant type. See [Auth](auth.md) for grant-specific runtime behavior.

```ts
interface OAuth2Config {
  type: 'oauth2';
  disabled?: boolean;
  grantType: 'authorization_code' | 'client_credentials' | 'password' | 'implicit';
  accessTokenUrl?: string;
  authorizationUrl?: string;
  clientId?: string;
  clientSecret?: string;
  clientIdIssuedAt?: number;
  clientSecretExpiresAt?: number;
  audience?: string;
  scope?: string;
  resource?: string;
  username?: string;
  password?: string;
  redirectUrl?: string;
  useDefaultBrowser?: boolean;
  credentialsInBody?: boolean;
  state?: string;
  code?: string;
  accessToken?: string;
  refreshToken?: string;
  tokenPrefix?: string;
  usePkce?: boolean;
  pkceMethod?: 'S256' | 'plain';
  responseType?: 'code' | 'id_token' | 'id_token token' | 'none' | 'token';
  origin?: string;
}
```

Set it via `--auth "oauth2:key=value;key2=value2;..."` on `request create` / `request update` / `request run`.
`grantType` defaults to `authorization_code` if omitted. Booleans (`disabled`,
`useDefaultBrowser`, `credentialsInBody`, `usePkce`) and numbers (`clientIdIssuedAt`,
`clientSecretExpiresAt`) are coerced automatically; all other fields are strings. Unknown keys
are rejected.

```bash
koh request create --name "Login" --workspace <id|name> \
  --auth "oauth2:grantType=authorization_code;authorizationUrl=https://auth.example.com/authorize;accessTokenUrl=https://auth.example.com/token;clientId=abc123;usePkce=true" \
  --project <path> --agent

koh request create --name "Service API" --workspace <id|name> \
  --auth "oauth2:grantType=client_credentials;accessTokenUrl=https://auth.example.com/oauth/token;clientId=svc-client;clientSecret=shh;scope=read:api" \
  --project <path> --agent

koh request create --name "Password Grant API" --workspace <id|name> \
  --auth "oauth2:grantType=password;accessTokenUrl=https://auth.example.com/oauth/token;clientId=app-client;clientSecret=shh;username=alice;password=secret;scope=read:api" \
  --project <path> --agent

koh request create --name "SPA Login" --workspace <id|name> \
  --auth "oauth2:grantType=implicit;authorizationUrl=https://auth.example.com/authorize;clientId=spa-client;responseType=token;redirectUrl=https://app.example.com/callback;scope=read:api" \
  --project <path> --agent
```

The shared fields above are accepted by the CLI schema. Runtime support, required fields, cache
behavior, and interactive resume data are documented per grant in [Auth](auth.md).

## request list

```bash
koh request list --project <path> --agent
koh request list [--workspace <id|name>] --project <path> --agent
koh request list [--query <text>] --project <path> --agent
```

| Option                     | Notes                                                                                     |
| -------------------------- | ----------------------------------------------------------------------------------------- |
| `[--workspace <id\|name>]` | Scope to a specific workspace                                                             |
| `[--query <text>]`         | Case-insensitive match across name, description, method, URL, headers, params, body, auth |

Returns:

```ts
{ data: Request[] }
```

## request show

```bash
koh request show <id|name> --project <path> --agent
koh request show <id|name> [--workspace <id|name>] --project <path> --agent
```

| Option                     | Notes                         |
| -------------------------- | ----------------------------- |
| `[--workspace <id\|name>]` | Scope lookup to one workspace |

Returns:

```ts
{
  data: Request;
}
```

## request create

```bash
koh request create --name <name> [--workspace <id|name>] --project <path> --agent
koh request create --name <name> [--parent <id>] --project <path> --agent
```

| Option                                | Notes                                                                                                                                                                                                                        |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--name <name>`                       | Request name (required)                                                                                                                                                                                                      |
| `[--workspace <id\|name>]`            | Requires `--workspace` or `--parent`                                                                                                                                                                                         |
| `[--parent <id>]`                     | Parent folder or workspace ID; defaults to workspace root when `--workspace` given                                                                                                                                           |
| `[--method <method>]`                 | HTTP method; default: `GET`                                                                                                                                                                                                  |
| `[--url <url>]`                       | Request URL                                                                                                                                                                                                                  |
| `[--description <desc>]`              | Request description                                                                                                                                                                                                          |
| `[-H, --header <header...>]`          | Headers; format: `"Name: Value"`; repeatable                                                                                                                                                                                 |
| `[-p, --param <param...>]`            | Query params; format: `"name=value"`; repeatable                                                                                                                                                                             |
| `[--path-param <pathParam...>]`       | Path params; format: `"name=value"`; repeatable                                                                                                                                                                              |
| `[--body <body>]`                     | Request body string                                                                                                                                                                                                          |
| `[--mime <type>]`                     | Body MIME type; default: `application/json`                                                                                                                                                                                  |
| `[--auth <auth>]`                     | `none` \| `bearer:<token>` \| `basic:<user>:<pass>` \| `digest:<user>:<pass>` \| `apikey:<key>:<value>[:<addTo>]` \| `oauth1:key=value;...` \| `oauth2:key=value;...` (see "OAuth1/OAuth2 request auth configuration" above) |
| `[--setting-send-cookies <boolean>]`  | `true`/`false`; sets `settings.cookies.send`                                                                                                                                                                                 |
| `[--setting-store-cookies <boolean>]` | `true`/`false`; sets `settings.cookies.store`                                                                                                                                                                                |

Returns:

```ts
{
  data: Request;
}
```

## request update

```bash
koh request update <id|name> --project <path> --agent
koh request update <id|name> [--workspace <id|name>] --project <path> --agent
```

| Option                                | Notes                                                                                                                                                                                                                        |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `[--workspace <id\|name>]`            | Scope lookup to one workspace                                                                                                                                                                                                |
| `[--name <name>]`                     | New request name                                                                                                                                                                                                             |
| `[--method <method>]`                 | HTTP method                                                                                                                                                                                                                  |
| `[--url <url>]`                       | Request URL                                                                                                                                                                                                                  |
| `[--description <desc>]`              | Request description                                                                                                                                                                                                          |
| `[-H, --header <header...>]`          | Replace all headers; format: `"Name: Value"`; repeatable                                                                                                                                                                     |
| `[-p, --param <param...>]`            | Replace all query params; format: `"name=value"`; repeatable                                                                                                                                                                 |
| `[--path-param <pathParam...>]`       | Replace all path params; format: `"name=value"`; repeatable                                                                                                                                                                  |
| `[--body <body>]`                     | Request body string                                                                                                                                                                                                          |
| `[--mime <type>]`                     | Body MIME type (used with `--body`)                                                                                                                                                                                          |
| `[--auth <auth>]`                     | `none` \| `bearer:<token>` \| `basic:<user>:<pass>` \| `digest:<user>:<pass>` \| `apikey:<key>:<value>[:<addTo>]` \| `oauth1:key=value;...` \| `oauth2:key=value;...` (see "OAuth1/OAuth2 request auth configuration" above) |
| `[--setting-send-cookies <boolean>]`  | `true`/`false`; sets `settings.cookies.send`                                                                                                                                                                                 |
| `[--setting-store-cookies <boolean>]` | `true`/`false`; sets `settings.cookies.store`                                                                                                                                                                                |

Only specified options are updated; unspecified fields remain unchanged.

Returns:

```ts
{
  data: Request;
}
```

## request run

```bash
koh request run <id|name> --project <path> --agent
koh request run <id|name> [--workspace <id|name>] [options] --project <path> --agent
```

| Option                                 | Notes                                                                                                                                                                                                  |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `[--workspace <id\|name>]`             | Scope request lookup to a single workspace                                                                                                                                                             |
| `[--project-environment <id\|name>]`   | Project environment or sub-environment used to render `{{ variable }}` templates                                                                                                                       |
| `[--workspace-environment <id\|name>]` | Workspace environment or sub-environment from the request's workspace used to render `{{ variable }}` templates; overrides project variables                                                           |
| `[--url <url>]`                        | Override request URL for this run only                                                                                                                                                                 |
| `[--method <method>]`                  | Override HTTP method for this run only                                                                                                                                                                 |
| `[-H, --header <header...>]`           | Override headers for this run only; replaces all stored headers; format: `"Name: Value"`; repeatable                                                                                                   |
| `[-p, --param <param...>]`             | Override query params for this run only; replaces all stored params; format: `"name=value"`; repeatable                                                                                                |
| `[--path-param <pathParam...>]`        | Override path params for this run only; replaces all stored path params; format: `"name=value"`; repeatable                                                                                            |
| `[--body <body>]`                      | Override request body for this run only; mutually exclusive with `--file-body`                                                                                                                         |
| `[--file-body <path>]`                 | Override request body with a file for this run only; path relative to cwd or absolute; requires `--data-folder` to allow access; mutually exclusive with `--body`                                      |
| `[--mime <type>]`                      | Override body MIME type for this run only (used with `--body` or `--file-body`)                                                                                                                        |
| `[--auth <auth>]`                      | Override auth for this run only; `none` \| `bearer:<token>` \| `basic:<user>:<pass>` \| `digest:<user>:<pass>` \| `apikey:<key>:<value>[:<addTo>]` \| `oauth1:key=value;...` \| `oauth2:key=value;...` |
| `[--body-output <mode>]`               | `auto` inlines small text bodies and writes large or binary bodies to a temp file; `file` always writes the body to a temp file                                                                        |
| `[--max-body-bytes <bytes>]`           | Maximum inline body size for `auto`; default: `512`                                                                                                                                                    |
| `[--data-folder <folder...>]`          | Directories that file references (`--file-body`, stored file body) may read from. Absolute or relative to cwd; repeatable. Required for file-body requests.                                            |

Override options replace the corresponding stored field entirely for this run; the stored request is not modified.

Before sending, `request run` renders `{{ variable }}` templates once across outgoing request strings: URL, header values, query and path parameter values, body, etc. Only environment variables template are supported for now.

See [Environments](environments.md) for default environment selection and merge precedence.

Returns:

```ts
{
  data: Response;
}
```

OAuth2 `authorization_code`, `client_credentials`, `password`, and `implicit` requests fetch and
cache tokens automatically. If an `authorization_code` or `implicit` request has no cached token,
`request run` returns a `Response` with `errorCode: 'interactive_auth_required'` and
`errorData.authorizeUrl`, `errorData.sessionId`, and `errorData.resumeCommand`; see [Auth](auth.md)
for the full interactive flow (`implicit` resumes with `auth complete --redirect-url`).
`client_credentials` and `password` requests fetch tokens non-interactively during `request run`.

## request remove

```bash
koh request remove <id|name> --project <path> --agent
koh request remove <id|name> [--workspace <id|name>] --project <path> --agent
```

**Warning**: Permanently removes the request.

| Option                     | Notes                         |
| -------------------------- | ----------------------------- |
| `[--workspace <id\|name>]` | Scope lookup to one workspace |

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
