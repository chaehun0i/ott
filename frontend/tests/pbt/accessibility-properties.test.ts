import fc from "fast-check";
import { errorReferenceGraph } from "@/shared/ui/primitives";

it("P-U01-09 generates unique resolvable error references", () => {
  fc.assert(
    fc.property(
      fc.uniqueArray(fc.string({ minLength: 1, maxLength: 12 }), { maxLength: 20 }),
      (names) => {
        const graph = errorReferenceGraph(names);
        expect(new Set(graph.map((item) => item.controlId)).size).toBe(graph.length);
        expect(new Set(graph.map((item) => item.errorId)).size).toBe(graph.length);
        expect(graph.every((item) => item.controlId !== item.errorId)).toBe(true);
      },
    ),
  );
});
