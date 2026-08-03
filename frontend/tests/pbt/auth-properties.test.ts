import fc from "fast-check";
import {
  createPendingIntent,
  transitionLogin,
  type LoginEvent,
} from "@/features/auth/pending-intent";

it("P-U01-06 executes zero times on failure and exactly once after any success", () => {
  const events = fc.array(fc.constantFrom<LoginEvent>("begin", "fail", "retry", "succeed"), {
    maxLength: 40,
  });
  fc.assert(
    fc.property(events, (sequence) => {
      let model = {
        authenticated: false,
        executionCount: 0,
        intent: createPendingIntent("save", "content", "/feed"),
      };
      for (const event of sequence) model = transitionLogin(model, event);
      expect(model.executionCount).toBe(sequence.includes("succeed") ? 1 : 0);
    }),
  );
});
