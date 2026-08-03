import { render, screen } from "@testing-library/react";
import { App } from "./App";

it("renders the application heading", () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: "OTT Feed" })).toBeInTheDocument();
});
