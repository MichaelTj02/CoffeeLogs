import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { register } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Register from "@/pages/register";

const mockReplace = jest.fn();

jest.mock("next/router", () => ({
  useRouter: () => ({ pathname: "/register", replace: mockReplace }),
}));

jest.mock("@/lib/api");
jest.mock("@/lib/auth");

const USER = { id: 1, email: "drinker@example.com" };

const signIn = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
  useAuth.mockReturnValue({ signIn });
});

describe("Register page", () => {
  it("renders the registration form", () => {
    render(<Register />);

    expect(screen.getByRole("heading", { name: "Create an account" })).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create account" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute("href", "/login");
  });

  it("trims the email but not the password, then signs in and navigates", async () => {
    register.mockResolvedValue(USER);
    const user = userEvent.setup();
    render(<Register />);

    await user.type(screen.getByLabelText(/Email/), "  drinker@example.com  ");
    await user.type(screen.getByLabelText(/Password/), "  spaced pw  ");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(register).toHaveBeenCalledWith("drinker@example.com", "  spaced pw  ");
    expect(signIn).toHaveBeenCalledWith(USER);
    expect(mockReplace).toHaveBeenCalledWith("/");
  });

  it("surfaces a duplicate-email conflict as a notice", async () => {
    const conflict = new Error("Email already registered");
    conflict.status = 409;
    register.mockRejectedValue(conflict);
    const user = userEvent.setup();
    render(<Register />);

    await user.type(screen.getByLabelText(/Email/), "drinker@example.com");
    await user.type(screen.getByLabelText(/Password/), "hunter22");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByText("Email already registered")).toHaveClass(
      "notice",
      "error"
    );
    expect(signIn).not.toHaveBeenCalled();
    expect(mockReplace).not.toHaveBeenCalled();
  });

  it("surfaces the short-password 422 the server owns", async () => {
    const invalid = new Error("String should have at least 8 characters");
    invalid.status = 422;
    register.mockRejectedValue(invalid);
    const user = userEvent.setup();
    render(<Register />);

    await user.type(screen.getByLabelText(/Email/), "drinker@example.com");
    await user.type(screen.getByLabelText(/Password/), "short");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(
      await screen.findByText("String should have at least 8 characters")
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create account" })).toBeEnabled();
  });
});
