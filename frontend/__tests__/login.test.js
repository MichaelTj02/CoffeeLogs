import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { login } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Login from "@/pages/login";

const mockReplace = jest.fn();

jest.mock("next/router", () => ({
  useRouter: () => ({ pathname: "/login", replace: mockReplace }),
}));

jest.mock("@/lib/api");
jest.mock("@/lib/auth");

const USER = { id: 1, email: "drinker@example.com" };

const signIn = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
  useAuth.mockReturnValue({ signIn });
});

describe("Login page", () => {
  it("renders the sign-in form", () => {
    render(<Login />);

    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Create one" })).toHaveAttribute(
      "href",
      "/register"
    );
  });

  it("trims the email but not the password, then signs in and navigates", async () => {
    login.mockResolvedValue(USER);
    const user = userEvent.setup();
    render(<Login />);

    await user.type(screen.getByLabelText(/Email/), "  drinker@example.com  ");
    await user.type(screen.getByLabelText(/Password/), "  spaced pw  ");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(login).toHaveBeenCalledWith("drinker@example.com", "  spaced pw  ");
    expect(signIn).toHaveBeenCalledWith(USER);
    expect(mockReplace).toHaveBeenCalledWith("/");
  });

  it("surfaces an API error as a notice and stays put", async () => {
    login.mockRejectedValue(new Error("Incorrect email or password"));
    const user = userEvent.setup();
    render(<Login />);

    await user.type(screen.getByLabelText(/Email/), "drinker@example.com");
    await user.type(screen.getByLabelText(/Password/), "wrong");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Incorrect email or password")).toHaveClass(
      "notice",
      "error"
    );
    expect(signIn).not.toHaveBeenCalled();
    expect(mockReplace).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled();
  });
});
