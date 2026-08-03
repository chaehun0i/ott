import type { QueryClient } from "@tanstack/react-query";
import type { RemoteResource } from "@/shared/model/presentation";

export type ProtectedNamespace = "member" | "recommendation" | "admin" | "personalization";
export type ProtectedEvent =
  "logout" | "consent-withdrawn" | "recommendation-reset" | "admin-forbidden";

export interface ProtectedState {
  admin: ReadonlySet<string>;
  member: ReadonlySet<string>;
  pendingFeedback: ReadonlySet<string>;
  personalization: ReadonlySet<string>;
  recommendation: ReadonlySet<string>;
}

export const emptyProtectedState = (): ProtectedState => ({
  admin: new Set(),
  member: new Set(),
  pendingFeedback: new Set(),
  personalization: new Set(),
  recommendation: new Set(),
});

export function purgeProtectedState(state: ProtectedState, event: ProtectedEvent): ProtectedState {
  if (event === "logout") return emptyProtectedState();
  if (event === "consent-withdrawn") {
    return {
      ...state,
      personalization: new Set(),
      pendingFeedback: new Set(),
      recommendation: new Set(),
    };
  }
  if (event === "recommendation-reset") return { ...state, recommendation: new Set() };
  return { ...state, admin: new Set() };
}

const namespaceByEvent: Record<ProtectedEvent, ProtectedNamespace[]> = {
  logout: ["member", "recommendation", "admin", "personalization"],
  "consent-withdrawn": ["recommendation", "personalization"],
  "recommendation-reset": ["recommendation"],
  "admin-forbidden": ["admin"],
};

export async function purgeQueryNamespaces(
  client: QueryClient,
  event: ProtectedEvent,
): Promise<void> {
  for (const namespace of namespaceByEvent[event]) {
    await client.cancelQueries({ queryKey: [namespace] });
    client.removeQueries({ queryKey: [namespace] });
  }
}

export function validRemoteResource<T>(resource: RemoteResource<T>): boolean {
  if (resource.status !== "stale" && resource.status !== "degraded") return true;
  return resource.data !== undefined && Boolean(resource.fetchedAt && resource.reason);
}
