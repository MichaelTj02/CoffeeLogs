// Shared display and form helpers, used by every page.

// An empty <input> yields "", and Pydantic rejects "" for `date | None` / `float | None`
// with a 422. Optional fields must send null. This is the most common source of mystery
// 422s in this stack, so all three pages go through these helpers.
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

export function formatDate(value) {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function formatDateTime(value) {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatPrice(value) {
  if (value === null || value === undefined) return null;
  return `$${Number(value).toFixed(2)}`;
}

// Brew ratio, the number you actually compare between attempts.
export function brewRatio(dose, yieldGrams) {
  if (!dose || !yieldGrams) return null;
  return `1:${(yieldGrams / dose).toFixed(1)}`;
}

export function stars(rating) {
  if (!rating) return null;
  return "★".repeat(rating) + "☆".repeat(5 - rating);
}
