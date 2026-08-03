const allowedNames = new Set(["web_vital", "route_outcome", "api_outcome", "ui_error"]);
const forbidden = /token|authorization|cookie|prompt|query|body|user[_-]?id/i;
export interface TelemetryEvent {
  name: string;
  route: string;
  outcome: string;
  value?: number;
}

export function sanitizeTelemetry(input: Record<string, unknown>): TelemetryEvent | undefined {
  if (
    !allowedNames.has(String(input.name)) ||
    Object.keys(input).some((key) => forbidden.test(key))
  )
    return undefined;
  const route = (typeof input.route === "string" ? input.route : "unknown").replace(
    /\/[0-9a-f-]{8,}/gi,
    "/:id",
  );
  const outcome = typeof input.outcome === "string" ? input.outcome : "unknown";
  return {
    name: String(input.name),
    route,
    outcome,
    ...(typeof input.value === "number" ? { value: input.value } : {}),
  };
}

export class TelemetryBuffer {
  readonly #events: TelemetryEvent[] = [];
  constructor(private readonly limit = 50) {}
  add(event: TelemetryEvent): boolean {
    if (this.#events.length >= this.limit) return false;
    this.#events.push(event);
    return true;
  }
  flush(endpoint = "/api/v1/telemetry/browser"): void {
    if (this.#events.length === 0) return;
    const body = JSON.stringify(this.#events.splice(0));
    try {
      if (!navigator.sendBeacon(endpoint, body))
        void fetch(endpoint, {
          method: "POST",
          body,
          keepalive: true,
          headers: { "content-type": "application/json" },
        }).catch(() => undefined);
    } catch {
      /* telemetry never blocks a user journey */
    }
  }
}
