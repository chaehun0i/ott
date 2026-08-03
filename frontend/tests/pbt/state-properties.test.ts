import fc from "fast-check";
import {
  emptyProtectedState,
  purgeProtectedState,
  validRemoteResource,
  type ProtectedEvent,
} from "@/shared/state/protected-state";

const eventArbitrary = fc.constantFrom<ProtectedEvent>(
  "logout",
  "consent-withdrawn",
  "recommendation-reset",
  "admin-forbidden",
);

it("P-U01-05 consent withdrawal removes every personalization-derived set", () => {
  fc.assert(
    fc.property(fc.array(fc.string(), { maxLength: 20 }), (ids) => {
      const state = {
        ...emptyProtectedState(),
        personalization: new Set(ids),
        pendingFeedback: new Set(ids),
        recommendation: new Set(ids),
      };
      const result = purgeProtectedState(state, "consent-withdrawn");
      expect(
        result.personalization.size + result.pendingFeedback.size + result.recommendation.size,
      ).toBe(0);
    }),
  );
});

it("P-U01-07 recommendation reset always reaches the same empty recommendation state", () => {
  fc.assert(
    fc.property(fc.array(fc.string(), { maxLength: 20 }), (ids) => {
      const state = { ...emptyProtectedState(), recommendation: new Set(ids) };
      expect(purgeProtectedState(state, "recommendation-reset").recommendation.size).toBe(0);
    }),
  );
});

it("P-U01-08 stale/degraded resources require data, time and reason", () => {
  fc.assert(
    fc.property(
      fc.constantFrom("stale" as const, "degraded" as const),
      fc.option(fc.string(), { nil: undefined }),
      (status, data) => {
        expect(validRemoteResource({ status, data })).toBe(false);
        expect(
          validRemoteResource({
            status,
            data: data ?? "cached",
            fetchedAt: "2026-08-03T00:00:00Z",
            reason: "network",
          }),
        ).toBe(true);
      },
    ),
  );
});

it("P-U01-10 logout removes all protected state after any event sequence", () => {
  fc.assert(
    fc.property(
      fc.array(eventArbitrary, { maxLength: 30 }),
      fc.array(fc.string(), { maxLength: 10 }),
      (events, ids) => {
        let state = {
          admin: new Set(ids),
          member: new Set(ids),
          pendingFeedback: new Set(ids),
          personalization: new Set(ids),
          recommendation: new Set(ids),
        };
        for (const event of events) state = purgeProtectedState(state, event);
        state = purgeProtectedState(state, "logout");
        expect(Object.values(state).every((set) => set.size === 0)).toBe(true);
      },
    ),
  );
});
