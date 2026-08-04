export function blankToNull(value) {
  if (typeof value !== "string") return value ?? null;
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

export function numberOrNull(value) {
  const trimmed = typeof value === "string" ? value.trim() : value;
  if (trimmed === "" || trimmed === null || trimmed === undefined) return null;
  const parsed = Number(trimmed);
  return Number.isNaN(parsed) ? null : parsed;
}

const DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/;

export function formatDate(value) {
  if (!value) return null;
  // A date-only string parses as UTC midnight, which renders a day early west of UTC,
  // so build it as a local calendar date instead.
  const parts = typeof value === "string" ? value.match(DATE_ONLY) : null;
  const d = parts
    ? new Date(Number(parts[1]), Number(parts[2]) - 1, Number(parts[3]))
    : new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function formatPrice(value) {
  if (value === null || value === undefined) return null;
  return `$${Number(value).toFixed(2)}`;
}

export function brewRatio(dose, yieldGrams) {
  if (!dose || !yieldGrams) return null;
  return `1:${(yieldGrams / dose).toFixed(1)}`;
}

export function stars(rating) {
  if (!rating) return null;
  return "★".repeat(rating) + "☆".repeat(5 - rating);
}
