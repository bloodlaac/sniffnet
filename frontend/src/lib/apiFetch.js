const BASE_URL = "http://localhost:7142";

export async function apiFetch(path, { method = "GET", body, headers = {}, ...rest } = {}) {
  const config = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    ...rest,
  };

  if (body !== undefined) {
    config.body = typeof body === "string" ? body : JSON.stringify(body);
  }

  const res = await fetch(`${BASE_URL}${path}`, config);

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${method} ${path} → ${res.status}: ${text}`);
  }
  return await res.json();
}