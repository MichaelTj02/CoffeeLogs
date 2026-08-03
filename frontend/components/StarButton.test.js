import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import StarButton from "@/components/StarButton";

describe("StarButton", () => {
  it("renders a filled star when active", () => {
    render(<StarButton active onToggle={() => {}} />);

    const button = screen.getByRole("button", { name: "Remove from favourites" });
    expect(button).toHaveTextContent("★");
    expect(button).toHaveAttribute("aria-pressed", "true");
    expect(button).toHaveAttribute("title", "Remove from favourites");
    expect(button).toHaveClass("star", "active");
  });

  it("renders an empty star when inactive", () => {
    render(<StarButton active={false} onToggle={() => {}} />);

    const button = screen.getByRole("button", { name: "Add to favourites" });
    expect(button).toHaveTextContent("☆");
    expect(button).toHaveAttribute("aria-pressed", "false");
    expect(button).not.toHaveClass("active");
  });

  it("fires onToggle when clicked", async () => {
    const onToggle = jest.fn();
    const user = userEvent.setup();
    render(<StarButton active={false} onToggle={onToggle} />);

    await user.click(screen.getByRole("button"));

    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it("is disabled while busy", async () => {
    const onToggle = jest.fn();
    const user = userEvent.setup();
    render(<StarButton active={false} onToggle={onToggle} busy />);

    const button = screen.getByRole("button");
    expect(button).toBeDisabled();

    await user.click(button, { pointerEventsCheck: 0 });
    expect(onToggle).not.toHaveBeenCalled();
  });
});
