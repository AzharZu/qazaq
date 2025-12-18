const API_URL = "/api";
const BASE = `${API_URL}/admin`;

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    ...options,
  });

  const redirectedToLogin =
    response.redirected && response.url.includes("/login") ||
    [401, 403, 303].includes(response.status);

  if (redirectedToLogin) {
    window.location.href = "/login";
    return Promise.reject(new Error("Not authenticated"));
  }

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const data = await response.json();
      detail = data?.detail || detail;
    } catch {
      // ignore parse errors
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export function fetchBlocks(lessonId) {
  return request(`${BASE}/lessons/${lessonId}/blocks`);
}

export function createBlock(lessonId, payload) {
  return request(`${BASE}/lessons/${lessonId}/blocks`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateBlock(blockId, payload) {
  return request(`${BASE}/lessons/blocks/${blockId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteBlock(blockId) {
  return request(`${BASE}/lessons/blocks/${blockId}`, { method: "DELETE" });
}

export function duplicateBlock(blockId) {
  return request(`${BASE}/lessons/blocks/${blockId}/duplicate`, { method: "POST" });
}

export function reorderBlocks(lessonId, order) {
  return request(`${BASE}/lessons/${lessonId}/blocks/reorder`, {
    method: "POST",
    body: JSON.stringify({ order }),
  });
}
