import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";

it("renders navigation and the localized application heading", () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: "OTT 통합 피드", level: 1 })).toBeInTheDocument();
  expect(screen.getByRole("navigation", { name: "주요" })).toBeInTheDocument();
});

it("changes locale, prefetches and navigates through the shell", async () => {
  window.history.replaceState({}, "", "/feed");
  render(<App />);
  const user = userEvent.setup();
  await user.selectOptions(screen.getByRole("combobox", { name: "언어" }), "en");
  const search = screen.getByRole("link", { name: "Search" });
  await user.hover(search);
  await user.click(search);
  expect(await screen.findByRole("status", { name: "search results" })).toBeInTheDocument();
});
