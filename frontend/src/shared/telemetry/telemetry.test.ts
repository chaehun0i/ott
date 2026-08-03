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
