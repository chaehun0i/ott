export function prefetchRoute(path: string): void {
  if (path.startsWith("/search")) void import("./route-search");
  else if (path.startsWith("/content")) void import("./route-detail");
}
