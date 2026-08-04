import { sanitizeTelemetry, TelemetryBuffer } from "./telemetry";
it("allows bounded anonymous telemetry", () => {
  expect(
    sanitizeTelemetry({ name: "api_outcome", route: "/content/abcdef12", outcome: "ok" }),
  ).toEqual({ name: "api_outcome", route: "/content/:id", outcome: "ok" });
});
it("rejects sensitive fields and overflow", () => {
  expect(
    sanitizeTelemetry({ name: "ui_error", route: "/", outcome: "fail", prompt: "secret" }),
  ).toBeUndefined();
  const buffer = new TelemetryBuffer(1);
  expect(buffer.add({ name: "web_vital", route: "/", outcome: "ok" })).toBe(true);
  expect(buffer.add({ name: "web_vital", route: "/", outcome: "ok" })).toBe(false);
});

it("flushes with beacon and falls back safely to fetch", () => {
  const sendBeacon = vi.fn().mockReturnValueOnce(true).mockReturnValueOnce(false);
  const fetchMock = vi.fn().mockResolvedValue(new Response());
  Object.defineProperty(navigator, "sendBeacon", { configurable: true, value: sendBeacon });
  vi.stubGlobal("fetch", fetchMock);

  const buffer = new TelemetryBuffer();
  buffer.flush();
  buffer.add({ name: "route_outcome", route: "/feed", outcome: "ok", value: 1 });
  buffer.flush("/telemetry");
  expect(sendBeacon).toHaveBeenCalledWith("/telemetry", expect.any(String));
  buffer.add({ name: "ui_error", route: "/feed", outcome: "handled" });
  buffer.flush("/fallback");
  expect(fetchMock).toHaveBeenCalledWith("/fallback", expect.objectContaining({ method: "POST" }));
  vi.unstubAllGlobals();
});
