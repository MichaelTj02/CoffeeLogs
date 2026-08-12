import {
  createBean,
  createMethod,
  deleteBean,
  getBean,
  getBeans,
  getMe,
  login,
  logout,
  register,
  setFavourite,
} from "@/lib/api";

const API_URL = "http://localhost:8000";

function jsonResponse(body, { status = 200, statusText = "OK" } = {}) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    json: async () => body,
  };
}

function brokenBodyResponse({ status, statusText }) {
  return {
    ok: false,
    status,
    statusText,
    json: async () => {
      throw new SyntaxError("Unexpected end of JSON input");
    },
  };
}

beforeEach(() => {
  global.fetch = jest.fn();
});

afterEach(() => {
  jest.resetAllMocks();
  delete global.fetch;
});

describe("request", () => {
  it("returns parsed JSON on 200", async () => {
    global.fetch.mockResolvedValue(jsonResponse([{ id: 1, name: "Kenya AA" }]));

    await expect(getBeans()).resolves.toEqual([{ id: 1, name: "Kenya AA" }]);
  });

  it("returns null on 204 without reading a body", async () => {
    const res = jsonResponse(null, { status: 204, statusText: "No Content" });
    const spy = jest.spyOn(res, "json");
    global.fetch.mockResolvedValue(res);

    await expect(deleteBean(3)).resolves.toBeNull();
    expect(spy).not.toHaveBeenCalled();
  });

  it("throws a string detail with the status attached", async () => {
    global.fetch.mockResolvedValue(
      jsonResponse({ detail: "Bean not found" }, { status: 404, statusText: "Not Found" })
    );

    await expect(getBean(9)).rejects.toMatchObject({
      message: "Bean not found",
      status: 404,
    });
  });

  it("joins an array detail with a semicolon", async () => {
    global.fetch.mockResolvedValue(
      jsonResponse(
        {
          detail: [
            { msg: "Input should be a valid date" },
            { msg: "Field required" },
          ],
        },
        { status: 422, statusText: "Unprocessable Entity" }
      )
    );

    await expect(createBean({})).rejects.toMatchObject({
      message: "Input should be a valid date; Field required",
      status: 422,
    });
  });

  it("falls back to statusText when the body is not JSON", async () => {
    global.fetch.mockResolvedValue(
      brokenBodyResponse({ status: 500, statusText: "Internal Server Error" })
    );

    await expect(getBeans()).rejects.toMatchObject({
      message: "Internal Server Error",
      status: 500,
    });
  });

  it("falls back to a generic message when there is no statusText either", async () => {
    global.fetch.mockResolvedValue(brokenBodyResponse({ status: 500, statusText: "" }));

    await expect(getBeans()).rejects.toThrow("Request failed");
  });

  it("reports an unreachable API on network failure", async () => {
    global.fetch.mockRejectedValue(new TypeError("Failed to fetch"));

    await expect(getBeans()).rejects.toThrow(
      "Could not reach the API. Is the backend running on port 8000?"
    );
  });

  it("sends credentials on every request so the session cookie travels", async () => {
    global.fetch.mockResolvedValue(jsonResponse([]));

    await getBeans();
    await deleteBean(3);

    for (const call of global.fetch.mock.calls) {
      expect(call[1]).toEqual(expect.objectContaining({ credentials: "include" }));
    }
  });

  it("dispatches coffeelogs:unauthorized on 401 and still throws", async () => {
    global.fetch.mockResolvedValue(
      jsonResponse({ detail: "Not authenticated" }, { status: 401, statusText: "Unauthorized" })
    );
    const listener = jest.fn();
    window.addEventListener("coffeelogs:unauthorized", listener);

    await expect(getBeans()).rejects.toMatchObject({
      message: "Not authenticated",
      status: 401,
    });
    expect(listener).toHaveBeenCalledTimes(1);

    window.removeEventListener("coffeelogs:unauthorized", listener);
  });

  it("does not dispatch coffeelogs:unauthorized for other errors", async () => {
    global.fetch.mockResolvedValue(
      jsonResponse({ detail: "Bean not found" }, { status: 404, statusText: "Not Found" })
    );
    const listener = jest.fn();
    window.addEventListener("coffeelogs:unauthorized", listener);

    await expect(getBean(9)).rejects.toThrow("Bean not found");
    expect(listener).not.toHaveBeenCalled();

    window.removeEventListener("coffeelogs:unauthorized", listener);
  });
});

describe("auth helpers", () => {
  it("register posts the credentials to /auth/register", async () => {
    global.fetch.mockResolvedValue(
      jsonResponse({ id: 1, email: "a@b.com" }, { status: 201 })
    );

    await expect(register("a@b.com", "hunter22")).resolves.toEqual({
      id: 1,
      email: "a@b.com",
    });
    expect(global.fetch).toHaveBeenCalledWith(`${API_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email: "a@b.com", password: "hunter22" }),
    });
  });

  it("login posts the credentials to /auth/login", async () => {
    global.fetch.mockResolvedValue(jsonResponse({ id: 1, email: "a@b.com" }));

    await login("a@b.com", "hunter22");

    expect(global.fetch).toHaveBeenCalledWith(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email: "a@b.com", password: "hunter22" }),
    });
  });

  it("logout posts without a body and resolves to null on 204", async () => {
    global.fetch.mockResolvedValue(
      jsonResponse(null, { status: 204, statusText: "No Content" })
    );

    await expect(logout()).resolves.toBeNull();

    expect(global.fetch).toHaveBeenCalledWith(
      `${API_URL}/auth/logout`,
      expect.objectContaining({ method: "POST", credentials: "include" })
    );
    expect(global.fetch.mock.calls[0][1]).not.toHaveProperty("body");
  });

  it("getMe reads /auth/me without a method", async () => {
    global.fetch.mockResolvedValue(jsonResponse({ id: 1, email: "a@b.com" }));

    await expect(getMe()).resolves.toEqual({ id: 1, email: "a@b.com" });
    expect(global.fetch).toHaveBeenCalledWith(`${API_URL}/auth/me`, {
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    });
  });
});

describe("getBeans", () => {
  it("omits the query string when no options are given", async () => {
    global.fetch.mockResolvedValue(jsonResponse([]));

    await getBeans();

    expect(global.fetch).toHaveBeenCalledWith(`${API_URL}/beans`, expect.anything());
  });

  it("builds a query string from limit and sort", async () => {
    global.fetch.mockResolvedValue(jsonResponse([]));

    await getBeans(6, "recent");

    expect(global.fetch).toHaveBeenCalledWith(
      `${API_URL}/beans?limit=6&sort=recent`,
      expect.anything()
    );
  });

  it("includes only the parameters that are set", async () => {
    global.fetch.mockResolvedValue(jsonResponse([]));

    await getBeans(undefined, "favourites");

    expect(global.fetch).toHaveBeenCalledWith(
      `${API_URL}/beans?sort=favourites`,
      expect.anything()
    );
  });
});

describe("write helpers", () => {
  it("createBean posts a JSON body with the JSON content type", async () => {
    global.fetch.mockResolvedValue(jsonResponse({ id: 1 }, { status: 201 }));

    await createBean({ name: "Kenya AA", roaster: "Square Mile" });

    expect(global.fetch).toHaveBeenCalledWith(`${API_URL}/beans`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ name: "Kenya AA", roaster: "Square Mile" }),
    });
  });

  it("setFavourite patches the favourite flag", async () => {
    global.fetch.mockResolvedValue(jsonResponse({ id: 4, is_favourite: true }));

    await setFavourite(4, true);

    expect(global.fetch).toHaveBeenCalledWith(
      `${API_URL}/beans/4/favourite`,
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ is_favourite: true }),
      })
    );
  });

  it("createMethod posts the name under the bean path", async () => {
    global.fetch.mockResolvedValue(jsonResponse({ id: 2 }, { status: 201 }));

    await createMethod(7, "V60");

    expect(global.fetch).toHaveBeenCalledWith(
      `${API_URL}/beans/7/methods`,
      expect.objectContaining({ method: "POST", body: JSON.stringify({ name: "V60" }) })
    );
  });
});
