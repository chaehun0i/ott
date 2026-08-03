export type TransportOutcome<T> =
  | { kind: "success"; data: T; correlationId?: string }
  | { kind: "validation"; status: 400 | 422; correlationId?: string }
  | { kind: "unauthenticated"; status: 401; correlationId?: string }
  | { kind: "forbidden"; status: 403; correlationId?: string }
  | { kind: "conflict"; status: 409; correlationId?: string }
  | { kind: "rateLimited"; status: 429; correlationId?: string }
  | { kind: "serverFailure"; status: number; correlationId?: string }
  | { kind: "networkFailure" }
  | { kind: "aborted" };

export interface RequestOptions {
  body?: unknown;
  idempotencyKey?: string;
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  signal?: AbortSignal;
}

function correlation(response: Response): string | undefined {
  return response.headers.get("x-correlation-id") ?? undefined;
}

function classifiedFailure(status: number, correlationId?: string): TransportOutcome<never> {
  if (status === 401) return { kind: "unauthenticated", status, correlationId };
  if (status === 403) return { kind: "forbidden", status, correlationId };
  if (status === 409) return { kind: "conflict", status, correlationId };
  if (status === 429) return { kind: "rateLimited", status, correlationId };
  if (status === 400 || status === 422) return { kind: "validation", status, correlationId };
  return { kind: "serverFailure", status, correlationId };
}

export class ApiClient {
  readonly #basePath: string;
  readonly #fetch: typeof fetch;
  #csrfToken: string | undefined;

  constructor(basePath = "/api/v1", fetchImpl: typeof fetch = fetch) {
    this.#basePath = basePath.replace(/\/$/, "");
    this.#fetch = fetchImpl;
  }

  setCsrfToken(token: string): void {
    this.#csrfToken = token;
  }

  async request<T>(path: string, options: RequestOptions = {}): Promise<TransportOutcome<T>> {
    const method = options.method ?? "GET";
    const headers = new Headers({ Accept: "application/json" });
    if (options.body !== undefined) headers.set("content-type", "application/json");
    if (method !== "GET" && this.#csrfToken) headers.set("x-csrf-token", this.#csrfToken);
    if (options.idempotencyKey) headers.set("idempotency-key", options.idempotencyKey);
    try {
      const response = await this.#fetch(`${this.#basePath}${path}`, {
        method,
        headers,
        credentials: "same-origin",
        body: options.body === undefined ? undefined : JSON.stringify(options.body),
        signal: options.signal,
      });
      const correlationId = correlation(response);
      if (!response.ok) return classifiedFailure(response.status, correlationId);
      if (response.status === 204) return { kind: "success", data: undefined as T, correlationId };
      return { kind: "success", data: (await response.json()) as T, correlationId };
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === "AbortError") return { kind: "aborted" };
      return { kind: "networkFailure" };
    }
  }
}
