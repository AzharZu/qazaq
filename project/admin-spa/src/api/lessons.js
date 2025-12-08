const BASE = "/admin/api";

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "same-origin",
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
      // ignore parse errors, keep default detail
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export function fetchLessons() {
  return request(`${BASE}/lessons`);
}

export function fetchLesson(lessonId) {
  return request(`${BASE}/lessons/${lessonId}`);
}

export function updateLesson(lessonId, payload) {
  return request(`${BASE}/lessons/${lessonId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
