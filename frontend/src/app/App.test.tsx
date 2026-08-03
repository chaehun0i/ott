import { render, screen } from "@testing-library/react";
import { App } from "./App";

it("renders navigation and the localized application heading", () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: "OTT 통합 피드", level: 1 })).toBeInTheDocument();
  expect(screen.getByRole("navigation", { name: "주요" })).toBeInTheDocument();
});
