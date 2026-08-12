import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import Navbar from "@/components/Navbar";
import { useAuth } from "@/lib/auth";

const mockPush = jest.fn();

jest.mock("next/router", () => ({
  useRouter: () => ({ pathname: "/", push: mockPush }),
}));

jest.mock("@/lib/auth");

const USER = { id: 1, email: "drinker@example.com" };

const signOut = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
});

describe("Navbar", () => {
  it("shows the wordmark alone while bootstrapping", () => {
    useAuth.mockReturnValue({ user: null, loading: true, signOut });
    render(<Navbar />);

    expect(screen.getByRole("link", { name: "Coffee Logs" })).toHaveAttribute("href", "/");
    expect(screen.queryByRole("link", { name: "Logs" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Log out" })).not.toBeInTheDocument();
  });

  it("shows the wordmark alone when signed out", () => {
    useAuth.mockReturnValue({ user: null, loading: false, signOut });
    render(<Navbar />);

    expect(screen.getByRole("link", { name: "Coffee Logs" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Add bean" })).not.toBeInTheDocument();
  });

  it("shows the links, the email and a log-out button when signed in", () => {
    useAuth.mockReturnValue({ user: USER, loading: false, signOut });
    render(<Navbar />);

    expect(screen.getByRole("link", { name: "Add bean" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "Logs" })).toHaveAttribute("href", "/logs");
    expect(screen.getByText("drinker@example.com")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Log out" })).toBeInTheDocument();
  });

  it("logs out without navigating — AuthGuard owns the redirect", async () => {
    useAuth.mockReturnValue({ user: USER, loading: false, signOut });
    const user = userEvent.setup();
    render(<Navbar />);

    await user.click(screen.getByRole("button", { name: "Log out" }));

    expect(signOut).toHaveBeenCalledTimes(1);
    expect(mockPush).not.toHaveBeenCalled();
  });
});
