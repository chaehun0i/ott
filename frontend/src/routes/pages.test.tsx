import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { AccountPage, AdminPage, RecommendationPage, SearchPage } from "./pages";
import { FeedPage } from "./feed";

function renderRoute(node: React.ReactNode) {
  return render(<MemoryRouter>{node}</MemoryRouter>);
}
it("filters the feed", async () => {
  renderRoute(<FeedPage />);
  await userEvent.selectOptions(screen.getByRole("combobox", { name: "장르" }), "코미디");
  expect(screen.getByRole("link", { name: "퇴근길 웃음" })).toBeInTheDocument();
  expect(screen.queryByText("별빛 식당")).not.toBeInTheDocument();
});
it("searches normalized Korean text", async () => {
  renderRoute(<SearchPage />);
  await userEvent.type(screen.getByRole("textbox", { name: "제목이나 조건" }), "코미디");
  await userEvent.click(screen.getByRole("button", { name: "검색" }));
  expect(screen.getByRole("status")).toHaveTextContent("코미디");
});
it("announces recommendation results", async () => {
  renderRoute(<RecommendationPage />);
  await userEvent.type(screen.getByRole("textbox", { name: "보고 싶은 콘텐츠" }), "가벼운 코미디");
  await userEvent.click(screen.getByRole("button", { name: "추천받기" }));
  expect(screen.getByRole("status")).toHaveTextContent("2편");
  expect(screen.getByText(/메타데이터와 일치/)).toBeInTheDocument();
});
it("withdraws consent", async () => {
  renderRoute(<AccountPage />);
  await userEvent.click(screen.getByRole("button", { name: "개인화 동의 철회" }));
  expect(screen.getByRole("status")).toHaveTextContent("추천 데이터를 삭제");
});
it("does not disclose admin resources", () => {
  renderRoute(<AdminPage />);
  expect(screen.getByRole("alert")).toHaveTextContent("접근 권한이 없습니다");
});
