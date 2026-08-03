import { createPendingIntent, SingleFlightAuthentication, transitionLogin } from "./pending-intent";

it("consumes an intent once after successful login", () => {
  const initial = {
    authenticated: false,
    executionCount: 0,
    intent: createPendingIntent("save", "c1", "/feed"),
  };
  const success = transitionLogin(initial, "succeed");
  expect(success.executionCount).toBe(1);
  expect(transitionLogin(success, "succeed").executionCount).toBe(1);
});

it("coalesces concurrent authentication", async () => {
  const authenticate = vi.fn(() => Promise.resolve(true));
  const singleFlight = new SingleFlightAuthentication();
  await Promise.all([singleFlight.run(authenticate), singleFlight.run(authenticate)]);
  expect(authenticate).toHaveBeenCalledOnce();
});

it("rejects external return paths", () => {
  expect(() => createPendingIntent("save", "c1", "//evil.example")).toThrow();
});
