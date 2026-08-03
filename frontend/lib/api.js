// NEXT_PUBLIC_ is required to reach browser code, and is inlined at build time, not runtime.
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// FastAPI's `detail` is a string for HTTPException but an array of objects for 422s.
function messageFromDetail(detail, fallback) {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || String(d)).join("; ") || fallback;
  }
  return fallback;
}

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${API_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error("Could not reach the API. Is the backend running on port 8000?");
  }

  if (!res.ok) {
    let detail = null;
    try {
      detail = (await res.json()).detail;
    } catch {
      // no JSON body — fall through to the status text
    }
    const error = new Error(messageFromDetail(detail, res.statusText || "Request failed"));
    error.status = res.status;
    throw error;
  }

  // A 204 has no body, so res.json() would throw.
  if (res.status === 204) return null;
  return res.json();
}

export function getBeans(limit, sort) {
  const params = new URLSearchParams();
  if (limit) params.set("limit", limit);
  if (sort) params.set("sort", sort);
  const query = params.toString();
  return request(`/beans${query ? `?${query}` : ""}`);
}

export function createBean(data) {
  return request("/beans", { method: "POST", body: JSON.stringify(data) });
}

export function getBean(id) {
  return request(`/beans/${id}`);
}

export function deleteBean(id) {
  return request(`/beans/${id}`, { method: "DELETE" });
}

export function setFavourite(id, isFavourite) {
  return request(`/beans/${id}/favourite`, {
    method: "PATCH",
    body: JSON.stringify({ is_favourite: isFavourite }),
  });
}

export function createMethod(beanId, name) {
  return request(`/beans/${beanId}/methods`, {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function deleteMethod(methodId) {
  return request(`/methods/${methodId}`, { method: "DELETE" });
}

export function createAttempt(methodId, data) {
  return request(`/methods/${methodId}/attempts`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteAttempt(attemptId) {
  return request(`/attempts/${attemptId}`, { method: "DELETE" });
}
