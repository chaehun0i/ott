import { render, screen } from "@testing-library/react";
import { ErrorSummary, Field, RemoteRegion, errorReferenceGraph } from "./primitives";

it("connects field hints and errors and renders an error summary", () => {
  const { container } = render(
    <>
      <Field name="query" label="Query" hint="Helpful hint" error="Required">
        <input id="query" />
      </Field>
      <ErrorSummary errors={[{ fieldId: "query", message: "Fix query" }]} />
    </>,
  );
  expect(screen.getAllByRole("alert")[0]).toHaveTextContent("Required");
  expect(screen.getByRole("link", { name: "Fix query" })).toHaveAttribute("href", "#query");
  expect(container.querySelector("[data-describedby]")).toHaveAttribute("data-describedby");
});

it("renders loading, error and ready remote region states", () => {
  const { rerender } = render(
    <RemoteRegion label="Results" status="loading">
      Content
    </RemoteRegion>,
  );
  expect(screen.getByRole("region", { name: "Results" })).toHaveAttribute("aria-busy", "true");
  rerender(
    <RemoteRegion label="Results" status="error">
      Content
    </RemoteRegion>,
  );
  expect(screen.getByRole("alert")).toBeInTheDocument();
  rerender(
    <RemoteRegion label="Results" status="ready">
      Content
    </RemoteRegion>,
  );
  expect(screen.getByText("Content")).toBeInTheDocument();
});

it("generates stable field and error references", () => {
  expect(errorReferenceGraph(["genre", "duration"])).toEqual([
    { controlId: "field-0-genre", errorId: "error-0-genre" },
    { controlId: "field-1-duration", errorId: "error-1-duration" },
  ]);
});
