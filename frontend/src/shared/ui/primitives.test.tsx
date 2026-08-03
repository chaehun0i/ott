import axe from "axe-core";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button, Disclosure, LiveRegion, RemoteRegion } from "./primitives";

it("uses role and accessible name as the primary selector", async () => {
  const user = userEvent.setup();
  const action = vi.fn();
  render(<Button onClick={action}>저장</Button>);
  await user.click(screen.getByRole("button", { name: "저장" }));
  expect(action).toHaveBeenCalledOnce();
});

it("exposes disclosure and remote status semantics", async () => {
  const { container } = render(
    <>
      <Disclosure label="추천 근거">검증된 장르</Disclosure>
      <RemoteRegion label="추천 결과" status="stale">
        작품
      </RemoteRegion>
      <LiveRegion>1개 결과</LiveRegion>
    </>,
  );
  expect(screen.getByText("추천 근거")).toBeInTheDocument();
  expect(screen.getByRole("status")).toHaveTextContent("마지막으로");
  expect((await axe.run(container)).violations).toEqual([]);
});
