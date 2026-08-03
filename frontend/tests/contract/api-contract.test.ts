import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll } from "vitest";
import { ApiClient } from "@/shared/api/client";

const server = setupServer(
  http.get("http://localhost/api/v1/feed", () =>
    HttpResponse.json(
      { items: [], next_cursor: null },
      { headers: { "x-correlation-id": "feed-1" } },
    ),
  ),
);

beforeAll(() => {
  server.listen({ onUnhandledRequest: "error" });
});
afterEach(() => {
  server.resetHandlers();
});
afterAll(() => {
  server.close();
});

it("maps an OpenAPI-aligned feed response", async () => {
  const result = await new ApiClient("http://localhost/api/v1").request<{
    items: unknown[];
    next_cursor: string | null;
  }>("/feed");
  expect(result).toEqual({
    kind: "success",
    data: { items: [], next_cursor: null },
    correlationId: "feed-1",
  });
});

it.each([400, 401, 403, 409, 422, 429, 503])("classifies HTTP %s", async (status) => {
  server.use(http.get("http://localhost/api/v1/feed", () => new HttpResponse(null, { status })));
  const result = await new ApiClient("http://localhost/api/v1").request("/feed");
  expect(result.kind).not.toBe("success");
});
