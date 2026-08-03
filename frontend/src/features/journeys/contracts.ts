export type LoadState = "fresh" | "stale" | "degraded";
export interface VersionedMutation {
  expectedVersion: number;
  reason?: string;
}
export interface RecommendationTurn {
  id: string;
  prompt: string;
  conditions: readonly string[];
}

export class LatestRequest {
  #controller?: AbortController;
  next(): AbortSignal {
    this.#controller?.abort();
    this.#controller = new AbortController();
    return this.#controller.signal;
  }
  cancel(): void {
    this.#controller?.abort();
  }
}

export function assertVersion(current: number, mutation: VersionedMutation): void {
  if (current !== mutation.expectedVersion) throw new Error("VERSION_CONFLICT");
}

export function deduplicateTurns(turns: readonly RecommendationTurn[]): RecommendationTurn[] {
  return [...new Map(turns.map((turn) => [turn.id, turn])).values()];
}
