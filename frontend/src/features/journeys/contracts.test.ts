import { assertVersion, deduplicateTurns, LatestRequest } from "./contracts";

it("cancels a superseded search", () => {
  const latest = new LatestRequest();
  const first = latest.next();
  latest.next();
  expect(first.aborted).toBe(true);
});
it("rejects stale account and admin mutations", () => {
  expect(() => {
    assertVersion(3, { expectedVersion: 2, reason: "correction" });
  }).toThrow("VERSION_CONFLICT");
});
it("deduplicates recommendation turns", () => {
  expect(
    deduplicateTurns([
      { id: "r1", prompt: "bright", conditions: [] },
      { id: "r1", prompt: "bright", conditions: [] },
    ]),
  ).toHaveLength(1);
});
