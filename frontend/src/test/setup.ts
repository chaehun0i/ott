import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";
import fc from "fast-check";

fc.configureGlobal({ numRuns: 100, seed: 260726 });

afterEach(() => {
  cleanup();
});
