import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { deleteBean, getBeans, setFavourite } from "@/lib/api";
import Logs from "@/pages/logs";

jest.mock("@/lib/api");

const BEANS = [
  {
    id: 1,
    name: "Kenya AA",
    roaster: "Square Mile",
    origin: "Nyeri",
    roast_date: null,
    price: null,
    notes: null,
    is_favourite: true,
    method_count: 2,
  },
  {
    id: 2,
    name: "Brazil Cerrado",
    roaster: "Origin",
    origin: null,
    roast_date: null,
    price: null,
    notes: null,
    is_favourite: false,
    method_count: 0,
  },
];

beforeEach(() => {
  jest.clearAllMocks();
});

describe("Logs page", () => {
  it("shows the loading state, then a card per bean", async () => {
    getBeans.mockResolvedValue(BEANS);
    render(<Logs />);

    expect(screen.getByText("Loading…")).toBeInTheDocument();

    expect(await screen.findByRole("link", { name: "Kenya AA" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Brazil Cerrado" })).toBeInTheDocument();
    expect(screen.queryByText("Loading…")).not.toBeInTheDocument();
  });

  it("shows the empty state when nothing is logged", async () => {
    getBeans.mockResolvedValue([]);
    render(<Logs />);

    expect(await screen.findByText("Nothing logged yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Add your first bean/ })).toHaveAttribute(
      "href",
      "/"
    );
  });

  it("shows a notice when the fetch fails", async () => {
    getBeans.mockRejectedValue(new Error("Could not reach the API."));
    render(<Logs />);

    expect(await screen.findByText("Could not reach the API.")).toBeInTheDocument();
    expect(screen.getByText("Nothing logged yet")).toBeInTheDocument();
  });

  it("deletes a bean after confirmation and re-fetches", async () => {
    getBeans.mockResolvedValueOnce(BEANS).mockResolvedValueOnce([BEANS[1]]);
    deleteBean.mockResolvedValue(null);
    const confirmSpy = jest.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();
    render(<Logs />);

    await screen.findByRole("link", { name: "Kenya AA" });
    await user.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    await waitFor(() => expect(deleteBean).toHaveBeenCalledWith(1));
    expect(confirmSpy).toHaveBeenCalledWith(
      'Delete "Kenya AA"? Its brew methods and every attempt under them go too.'
    );
    expect(getBeans).toHaveBeenCalledTimes(2);
    await waitFor(() =>
      expect(screen.queryByRole("link", { name: "Kenya AA" })).not.toBeInTheDocument()
    );

    confirmSpy.mockRestore();
  });

  it("does not delete when the confirmation is dismissed", async () => {
    getBeans.mockResolvedValue(BEANS);
    const confirmSpy = jest.spyOn(window, "confirm").mockReturnValue(false);
    const user = userEvent.setup();
    render(<Logs />);

    await screen.findByRole("link", { name: "Kenya AA" });
    await user.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    expect(deleteBean).not.toHaveBeenCalled();
    expect(getBeans).toHaveBeenCalledTimes(1);

    confirmSpy.mockRestore();
  });

  it("surfaces a failed delete as a notice", async () => {
    getBeans.mockResolvedValue(BEANS);
    deleteBean.mockRejectedValue(new Error("Bean not found"));
    const confirmSpy = jest.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();
    render(<Logs />);

    await screen.findByRole("link", { name: "Kenya AA" });
    await user.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    expect(await screen.findByText("Bean not found")).toBeInTheDocument();

    confirmSpy.mockRestore();
  });

  it("flips the star optimistically and re-fetches", async () => {
    getBeans.mockResolvedValue(BEANS);
    setFavourite.mockResolvedValue({ ...BEANS[1], is_favourite: true });
    const user = userEvent.setup();
    render(<Logs />);

    await screen.findByRole("link", { name: "Brazil Cerrado" });
    await user.click(screen.getByRole("button", { name: "Add to favourites" }));

    await waitFor(() => expect(setFavourite).toHaveBeenCalledWith(2, true));
    expect(getBeans).toHaveBeenCalledTimes(2);
  });

  it("rolls the star back when the toggle fails", async () => {
    getBeans.mockResolvedValue(BEANS);
    setFavourite.mockRejectedValue(new Error("Bean not found"));
    const user = userEvent.setup();
    render(<Logs />);

    await screen.findByRole("link", { name: "Brazil Cerrado" });
    await user.click(screen.getByRole("button", { name: "Add to favourites" }));

    expect(await screen.findByText("Bean not found")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add to favourites" })).toBeInTheDocument();
  });
});
