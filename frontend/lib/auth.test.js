import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { getMe, logout } from "@/lib/api";
import { AuthProvider, useAuth } from "@/lib/auth";

jest.mock("@/lib/api");

const USER = { id: 1, email: "drinker@example.com", created_at: "2026-01-01T00:00:00Z" };

function Probe() {
  const { user, loading, signIn, signOut } = useAuth();

  return (
    <div>
      <p>loading: {String(loading)}</p>
      <p>user: {user ? user.email : "none"}</p>
      <button type="button" onClick={() => signIn({ id: 2, email: "other@example.com" })}>
        Sign in
      </button>
      <button type="button" onClick={signOut}>
        Sign out
      </button>
    </div>
  );
}

function renderProbe() {
  return render(
    <AuthProvider>
      <Probe />
    </AuthProvider>
  );
}

function unauthorized() {
  const error = new Error("Not authenticated");
  error.status = 401;
  return error;
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe("AuthProvider bootstrap", () => {
  it("stores the user and clears loading when getMe resolves", async () => {
    getMe.mockResolvedValue(USER);
    renderProbe();

    expect(screen.getByText("loading: true")).toBeInTheDocument();

    expect(await screen.findByText("loading: false")).toBeInTheDocument();
    expect(screen.getByText("user: drinker@example.com")).toBeInTheDocument();
    expect(getMe).toHaveBeenCalledTimes(1);
  });

  it("ends signed out when getMe 401s", async () => {
    getMe.mockRejectedValue(unauthorized());
    renderProbe();

    expect(await screen.findByText("loading: false")).toBeInTheDocument();
    expect(screen.getByText("user: none")).toBeInTheDocument();
  });

  it("ends signed out — not a stuck spinner — when the API is unreachable", async () => {
    getMe.mockRejectedValue(new Error("Could not reach the API."));
    renderProbe();

    expect(await screen.findByText("loading: false")).toBeInTheDocument();
    expect(screen.getByText("user: none")).toBeInTheDocument();
  });
});

describe("AuthProvider session changes", () => {
  it("drops the user on a coffeelogs:unauthorized event", async () => {
    getMe.mockResolvedValue(USER);
    renderProbe();
    await screen.findByText("user: drinker@example.com");

    await act(async () => {
      window.dispatchEvent(new Event("coffeelogs:unauthorized"));
    });

    expect(screen.getByText("user: none")).toBeInTheDocument();
  });

  it("signIn stores the user the endpoint returned", async () => {
    getMe.mockRejectedValue(unauthorized());
    const user = userEvent.setup();
    renderProbe();
    await screen.findByText("user: none");

    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(screen.getByText("user: other@example.com")).toBeInTheDocument();
  });

  it("signOut calls the API and clears the user", async () => {
    getMe.mockResolvedValue(USER);
    logout.mockResolvedValue(null);
    const user = userEvent.setup();
    renderProbe();
    await screen.findByText("user: drinker@example.com");

    await user.click(screen.getByRole("button", { name: "Sign out" }));

    expect(logout).toHaveBeenCalledTimes(1);
    expect(screen.getByText("user: none")).toBeInTheDocument();
  });

  it("signOut clears the user even when the API call fails", async () => {
    getMe.mockResolvedValue(USER);
    logout.mockRejectedValue(new Error("Could not reach the API."));
    const user = userEvent.setup();
    renderProbe();
    await screen.findByText("user: drinker@example.com");

    await user.click(screen.getByRole("button", { name: "Sign out" }));

    expect(screen.getByText("user: none")).toBeInTheDocument();
  });
});
