/**
 * Typed fetch wrapper for the BudgetApp REST API.
 *
 * - Reads the API base URL from `import.meta.env.VITE_API_URL`, falling back
 *   to the dev default `http://localhost:8000/api/v1`.
 * - Sends credentials so the session cookie set by Django flows with each
 *   request (SPEC section 5.1: session cookies for the SPA).
 * - Threads the CSRF token from the `csrftoken` cookie on unsafe methods
 *   (SPEC section 7.4).
 * - Throws a typed `ApiError` on non-2xx responses.
 *
 * TODO: personal access token (PAT) auth — used by external integrators per
 * SPEC section 5.1 — is intentionally not exercised from the SPA. The SPA
 * rides on session cookies; PATs are for CLI / Home Assistant / n8n / etc.
 */

const DEFAULT_BASE_URL = 'http://localhost:8000/api/v1';

const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

export interface ApiErrorBody {
  detail?: string;
  // DRF-style field errors: { field: ["error 1", "error 2"] }.
  [field: string]: unknown;
}

export class ApiError extends Error {
  readonly status: number;
  readonly body: ApiErrorBody | null;

  constructor(status: number, body: ApiErrorBody | null, message?: string) {
    super(message ?? body?.detail ?? `HTTP ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

export interface RequestOptions {
  /** Query string parameters. Values are stringified with `String()`. */
  query?: Record<string, string | number | boolean | undefined | null>;
  /** Extra headers merged after the defaults. */
  headers?: Record<string, string>;
  /** Optional fetch implementation (e.g. SvelteKit's load fetch). */
  fetch?: typeof fetch;
  /** Abort signal for cancellation. */
  signal?: AbortSignal;
}

function getBaseUrl(): string {
  const fromEnv = typeof import.meta !== 'undefined' ? import.meta.env?.VITE_API_URL : undefined;
  return (fromEnv ?? DEFAULT_BASE_URL).replace(/\/+$/, '');
}

function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const prefix = `${name}=`;
  for (const part of document.cookie.split(';')) {
    const trimmed = part.trim();
    if (trimmed.startsWith(prefix)) {
      return decodeURIComponent(trimmed.slice(prefix.length));
    }
  }
  return null;
}

function buildUrl(path: string, query?: RequestOptions['query']): string {
  const base = getBaseUrl();
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = `${base}${normalizedPath}`;
  if (!query) return url;

  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null) continue;
    params.append(key, String(value));
  }
  const qs = params.toString();
  return qs ? `${url}?${qs}` : url;
}

async function parseBody(response: Response): Promise<unknown> {
  if (response.status === 204) return null;
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  const text = await response.text();
  return text.length ? text : null;
}

async function request<T>(
  method: string,
  path: string,
  body: unknown,
  options: RequestOptions = {}
): Promise<T> {
  const fetchImpl = options.fetch ?? fetch;
  const url = buildUrl(path, options.query);

  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(options.headers ?? {})
  };

  let serializedBody: BodyInit | undefined;
  if (body !== undefined && body !== null) {
    if (body instanceof FormData || body instanceof Blob) {
      serializedBody = body;
    } else {
      headers['Content-Type'] ??= 'application/json';
      serializedBody = JSON.stringify(body);
    }
  }

  if (UNSAFE_METHODS.has(method)) {
    const csrf = readCookie('csrftoken');
    if (csrf && !headers['X-CSRFToken']) {
      headers['X-CSRFToken'] = csrf;
    }
  }

  const response = await fetchImpl(url, {
    method,
    headers,
    body: serializedBody,
    credentials: 'include',
    signal: options.signal
  });

  const parsed = await parseBody(response);

  if (!response.ok) {
    const errorBody = parsed && typeof parsed === 'object' ? (parsed as ApiErrorBody) : null;
    throw new ApiError(response.status, errorBody);
  }

  return parsed as T;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) => request<T>('GET', path, undefined, options),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>('POST', path, body, options),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>('PATCH', path, body, options),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>('PUT', path, body, options),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>('DELETE', path, undefined, options)
};

export type Api = typeof api;
