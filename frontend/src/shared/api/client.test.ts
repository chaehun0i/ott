import { ApiClient } from "./client";

it("classifies authorization failures without reading response bodies", async () => {
  const fetchMock = vi
    .fn<typeof fetch>()
    .mockResolvedValue(
      new Response("secret", { status: 403, headers: { "x-correlation-id": "safe-ref" } }),
    );
  const result = await new ApiClient("/api/v1", fetchMock).request("/admin/incidents");
  expect(result).toEqual({ kind: "forbidden", status: 403, correlationId: "safe-ref" });
});

it("attaches CSRF only to mutations", async () => {
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(new Response(null, { status: 204 }));
  const client = new ApiClient("/api/v1", fetchMock);
  client.setCsrfToken("csrf-value");
  await client.request("/profile", { method: "PUT", body: { locale: "ko" } });
  const request = fetchMock.mock.calls[0]?.[1];
  expect(new Headers(request?.headers).get("x-csrf-token")).toBe("csrf-value");
  expect(request?.credentials).toBe("same-origin");
});

it("returns an aborted outcome", async () => {
  const fetchMock = vi
    .fn<typeof fetch>()
    .mockRejectedValue(new DOMException("cancel", "AbortError"));
  await expect(new ApiClient("/api/v1", fetchMock).request("/feed")).resolves.toEqual({
    kind: "aborted",
  });
});
