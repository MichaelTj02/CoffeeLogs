import { blankToNull, brewRatio, formatDate, formatPrice, numberOrNull, stars } from "@/lib/format";

const DATE_OPTIONS = { year: "numeric", month: "short", day: "numeric" };

describe("blankToNull", () => {
  it("trims and keeps non-empty strings", () => {
    expect(blankToNull("  Ethiopia  ")).toBe("Ethiopia");
  });

  it("returns null for empty and whitespace-only strings", () => {
    expect(blankToNull("")).toBeNull();
    expect(blankToNull("   ")).toBeNull();
  });

  it("returns null for null and undefined", () => {
    expect(blankToNull(null)).toBeNull();
    expect(blankToNull(undefined)).toBeNull();
  });

  it("passes non-string values through", () => {
    expect(blankToNull(12)).toBe(12);
    expect(blankToNull(false)).toBe(false);
  });
});

describe("numberOrNull", () => {
  it("parses numeric strings", () => {
    expect(numberOrNull(" 18.5 ")).toBe(18.5);
  });

  it("returns null for blank, null and undefined", () => {
    expect(numberOrNull("")).toBeNull();
    expect(numberOrNull("   ")).toBeNull();
    expect(numberOrNull(null)).toBeNull();
    expect(numberOrNull(undefined)).toBeNull();
  });

  it("returns null for unparseable strings", () => {
    expect(numberOrNull("abc")).toBeNull();
  });

  it("keeps numbers, including zero", () => {
    expect(numberOrNull(0)).toBe(0);
    expect(numberOrNull(42)).toBe(42);
  });
});

describe("formatDate", () => {
  it("renders a date-only string as that local calendar date", () => {
    const expected = new Date(2026, 0, 15).toLocaleDateString(undefined, DATE_OPTIONS);
    expect(formatDate("2026-01-15")).toBe(expected);
  });

  it("renders a full timestamp", () => {
    const value = "2026-01-15T09:30:00Z";
    const expected = new Date(value).toLocaleDateString(undefined, DATE_OPTIONS);
    expect(formatDate(value)).toBe(expected);
  });

  it("returns null for falsy and invalid input", () => {
    expect(formatDate(null)).toBeNull();
    expect(formatDate("")).toBeNull();
    expect(formatDate("not a date")).toBeNull();
  });
});

describe("formatPrice", () => {
  it("formats to two decimals", () => {
    expect(formatPrice(18.5)).toBe("$18.50");
    expect(formatPrice("7")).toBe("$7.00");
  });

  it("formats zero rather than dropping it", () => {
    expect(formatPrice(0)).toBe("$0.00");
  });

  it("returns null for null and undefined", () => {
    expect(formatPrice(null)).toBeNull();
    expect(formatPrice(undefined)).toBeNull();
  });
});

describe("brewRatio", () => {
  it("renders a one-decimal ratio", () => {
    expect(brewRatio(18, 300)).toBe("1:16.7");
    expect(brewRatio(20, 40)).toBe("1:2.0");
  });

  it("returns null when either side is missing or zero", () => {
    expect(brewRatio(0, 300)).toBeNull();
    expect(brewRatio(18, 0)).toBeNull();
    expect(brewRatio(null, undefined)).toBeNull();
  });
});

describe("stars", () => {
  it("fills the rating and pads to five", () => {
    expect(stars(3)).toBe("★★★☆☆");
    expect(stars(5)).toBe("★★★★★");
    expect(stars(1)).toBe("★☆☆☆☆");
  });

  it("returns null for no rating", () => {
    expect(stars(0)).toBeNull();
    expect(stars(null)).toBeNull();
  });
});
