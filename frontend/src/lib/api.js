const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function normalizePath(path = "") {
  return path.startsWith("/") ? path : `/${path}`;
}

async function parseResponse(res) {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch (err) {
    return text;
  }
}

async function api(path, options = {}) {
  const { headers, body, method = "GET", ...rest } = options;
  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;

  const response = await fetch(`${API_BASE_URL}${normalizePath(path)}`, {
    method,
    headers: isFormData
      ? headers
      : {
          "Content-Type": "application/json",
          ...headers,
        },
    body: body && !isFormData ? JSON.stringify(body) : body,
    ...rest,
  });

  const data = await parseResponse(response);

  if (!response.ok) {
    const message =
      (data && (data.detail || data.error || data.message)) ||
      `Запрос вернул ${response.status}`;
    const err = new Error(message);
    err.status = response.status;
    err.data = data;
    throw err;
  }

  return data;
}

export const login = (username, password) =>
  api("/auth/login", {
    method: "POST",
    body: { username, password },
  });

export const getDatasets = () => api("/datasets");
export const getModels = () => api("/models");
export const getConfigs = () => api("/configurations");
export const getExperiments = () => api("/experiments");
export const getExperiment = (id) => api(`/experiments/${id}`);

export const createExperiment = (payload) =>
  api("/experiments", {
    method: "POST",
    body: payload,
  });

export const predict = (file) => {
  const form = new FormData();
  form.append("file", file);

  return api("/api/predict", {
    method: "POST",
    body: form,
    headers: {},
  });
};

export { api, API_BASE_URL };
