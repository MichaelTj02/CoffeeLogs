import { render, screen } from "@testing-library/react";

import AuthGuard from "@/components/AuthGuard";
import { useAuth } from "@/lib/auth";

const mockReplace = jest.fn();
let mockPathname = "/";

// The suite has no router mocking otherwise; a per-file hand-rolled mock beats a dependency.
jest.mock("next/router", () => ({
  useRouter: () => ({ pathname: mockPathname, replace: mockReplace }),
}));

jest.mock("@/lib/auth");

const USER = { id: 1, email: "drinker@example.com" };

function renderGuard() {
  return render(
    <AuthGuard>
      <p>bean list</p>
    </AuthGuard>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  mockPathname = "/";
});

describe("AuthGuard", () => {
  it("renders the inert state while auth is bootstrapping", () => {
    useAuth.mockReturnValue({ user: null, loading: true });
    renderGuard();

    expect(screen.getByText("Loading…")).toHaveClass("state");
    expect(screen.queryByText("bean list")).not.toBeInTheDocument();
    expect(mockReplace).not.toHaveBeenCalled();
  });

  it("redirects to /login from a protected path and never mounts the page", () => {
    useAuth.mockReturnValue({ user: null, loading: false });
    renderGuard();

    expect(mockReplace).toHaveBeenCalledWith("/login");
    expect(screen.queryByText("bean list")).not.toBeInTheDocument();
    expect(screen.getByText("Loading…")).toHaveClass("state");
  });

  it("redirects a signed-in user away from a public path", () => {
    mockPathname = "/login";
    useAuth.mockReturnValue({ user: USER, loading: false });
    renderGuard();

    expect(mockReplace).toHaveBeenCalledWith("/");
    expect(screen.queryByText("bean list")).not.toBeInTheDocument();
  });

  it("renders children for a signed-in user on a protected path", () => {
    useAuth.mockReturnValue({ user: USER, loading: false });
    renderGuard();

    expect(screen.getByText("bean list")).toBeInTheDocument();
    expect(mockReplace).not.toHaveBeenCalled();
  });

  it("renders children for a signed-out user on a public path", () => {
    mockPathname = "/register";
    useAuth.mockReturnValue({ user: null, loading: false });
    renderGuard();

    expect(screen.getByText("bean list")).toBeInTheDocument();
    expect(mockReplace).not.toHaveBeenCalled();
  });
});
