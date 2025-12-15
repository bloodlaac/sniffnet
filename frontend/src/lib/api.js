const API_BASE = "/api";

async function handleJsonResponse(res) {
  let data = null;
  try {
    data = await res.json();
  } catch (err) {
    // ignore parse errors; will handle below
  }
  return data;
}

export async function prewarmModel() {
  const res = await fetch(`${API_BASE}/model/load`, { method: "POST" });
  const data = await handleJsonResponse(res);

  if (!res.ok) {
    const message = (data && (data.detail || data.error)) || `Failed to prewarm: ${res.status}`;
    const err = new Error(message);
    err.status = res.status;
    throw err;
  }

  return data;
}

export async function predictImage(file) {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    body: form,
  });

  const data = await handleJsonResponse(res);

  if (!res.ok) {
    const message = (data && (data.detail || data.error)) || `Prediction failed (${res.status})`;
    const err = new Error(message);
    err.status = res.status;
    throw err;
  }

  return data;
}

export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function predictWithRetry(
  file,
  { retries = 5, delayMs = 1200, onRetry } = {}
) {
  let attempt = 0;

  while (attempt <= retries) {
    try {
      return await predictImage(file);
    } catch (err) {
      const isLoading =
        err.status === 503 && err.message && err.message.toLowerCase().includes("loading");

      if (!isLoading || attempt === retries) {
        if (isLoading && attempt === retries) {
          throw new Error("Model is still loading, try again later.");
        }
        throw err;
      }

      if (typeof onRetry === "function") {
        onRetry(attempt + 1);
      }

      await sleep(delayMs);
      attempt += 1;
    }
  }

  throw new Error("Model is still loading, try again later.");
}
