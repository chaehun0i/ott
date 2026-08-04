import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { AccountPage, DetailPage, LoginPage, NotificationsPage, RecommendationPage } from "./pages";

function renderRoute(node: React.ReactNode) {
  return render(<MemoryRouter initialEntries={["/content/c1"]}>{node}</MemoryRouter>);
}

it("supports recommendation refinement and reset actions", async () => {
  renderRoute(<RecommendationPage />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button"));
  const article = await screen.findByRole("article");
  const actions = within(article).getAllByRole("button");
  await user.click(actions[0]);
  expect(screen.getByRole("status")).not.toBeEmptyDOMElement();
  await user.click(actions[1]);
  expect(screen.getByRole("status")).not.toBeEmptyDOMElement();
});

it("supports all account actions", async () => {
  renderRoute(<AccountPage />);
  const user = userEvent.setup();
  const buttons = screen.getAllByRole("button");
  for (const button of buttons) {
    await user.click(button);
    expect(screen.getByRole("status")).not.toBeEmptyDOMElement();
  }
});

it("renders detail external navigation and handles back", async () => {
  renderRoute(<DetailPage />);
  expect(screen.getByRole("link")).toHaveAttribute("rel", "noreferrer");
  await userEvent.click(screen.getByRole("button"));
});

it("renders login and notification controls", () => {
  const { rerender } = renderRoute(<LoginPage />);
  expect(screen.getByRole("button")).toBeEnabled();
  rerender(
    <MemoryRouter>
      <NotificationsPage />
    </MemoryRouter>,
  );
  expect(screen.getByRole("checkbox")).toBeEnabled();
});
