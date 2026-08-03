import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import BeanCard from "@/components/BeanCard";

const DATE_OPTIONS = { year: "numeric", month: "short", day: "numeric" };

function makeBean(overrides = {}) {
  return {
    id: 1,
    name: "Kenya AA",
    roaster: "Square Mile",
    origin: null,
    roast_date: null,
    price: null,
    notes: null,
    is_favourite: false,
    method_count: 0,
    ...overrides,
  };
}

describe("BeanCard", () => {
  it("links the name and the open button to the bean page", () => {
    render(<BeanCard bean={makeBean({ id: 12 })} />);

    expect(screen.getByRole("link", { name: "Kenya AA" })).toHaveAttribute(
      "href",
      "/beans/12"
    );
    expect(screen.getByRole("link", { name: "Open" })).toHaveAttribute("href", "/beans/12");
    expect(screen.getByText("Square Mile")).toBeInTheDocument();
  });

  it("omits meta rows whose values are missing", () => {
    render(<BeanCard bean={makeBean()} />);

    expect(screen.queryByText("Origin")).not.toBeInTheDocument();
    expect(screen.queryByText("Roasted")).not.toBeInTheDocument();
    expect(screen.queryByText("Price")).not.toBeInTheDocument();
    expect(screen.queryByText(/tastes like/i)).not.toBeInTheDocument();
  });

  it("renders meta rows and notes when values are present", () => {
    const bean = makeBean({
      origin: "Nyeri",
      roast_date: "2026-01-15",
      price: 18.5,
      notes: "Tastes like blackcurrant",
    });
    const expectedDate = new Date(2026, 0, 15).toLocaleDateString(undefined, DATE_OPTIONS);
    render(<BeanCard bean={bean} />);

    expect(screen.getByText("Origin")).toBeInTheDocument();
    expect(screen.getByText("Nyeri")).toBeInTheDocument();
    expect(screen.getByText("Roasted")).toBeInTheDocument();
    expect(screen.getByText(expectedDate)).toBeInTheDocument();
    expect(screen.getByText("Price")).toBeInTheDocument();
    expect(screen.getByText("$18.50")).toBeInTheDocument();
    expect(screen.getByText("Tastes like blackcurrant")).toBeInTheDocument();
  });

  it.each([
    [0, "0 methods"],
    [1, "1 method"],
    [2, "2 methods"],
  ])("pluralizes a method_count of %i", (count, expected) => {
    render(<BeanCard bean={makeBean({ method_count: count })} />);

    expect(screen.getByText(expected)).toBeInTheDocument();
  });

  it("treats a missing method_count as zero", () => {
    const bean = makeBean();
    delete bean.method_count;
    render(<BeanCard bean={bean} />);

    expect(screen.getByText("0 methods")).toBeInTheDocument();
  });

  it("marks favourites with a class", () => {
    const { container } = render(<BeanCard bean={makeBean({ is_favourite: true })} />);

    expect(container.querySelector("article")).toHaveClass("favourite");
  });

  it("hides the star and delete controls when no handlers are passed", () => {
    render(<BeanCard bean={makeBean()} />);

    expect(screen.queryByRole("button", { name: /favourites/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();
  });

  it("calls onToggleFavourite with the bean", async () => {
    const bean = makeBean();
    const onToggleFavourite = jest.fn();
    const user = userEvent.setup();
    render(<BeanCard bean={bean} onToggleFavourite={onToggleFavourite} />);

    await user.click(screen.getByRole("button", { name: "Add to favourites" }));

    expect(onToggleFavourite).toHaveBeenCalledWith(bean);
  });

  it("calls onDelete with the bean", async () => {
    const bean = makeBean();
    const onDelete = jest.fn();
    const user = userEvent.setup();
    render(<BeanCard bean={bean} onDelete={onDelete} />);

    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(onDelete).toHaveBeenCalledWith(bean);
  });

  it("disables the star while busy", () => {
    render(<BeanCard bean={makeBean()} onToggleFavourite={() => {}} busy />);

    expect(screen.getByRole("button", { name: "Add to favourites" })).toBeDisabled();
  });
});
