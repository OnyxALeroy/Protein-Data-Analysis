const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, opts = {}) {
  const res = await fetch(API_BASE + path, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText} - ${text}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  // Proteins
  searchProteins: (query, limit = 20, page = 1) =>
    request(
      `/proteins/?query=${encodeURIComponent(
        query || ""
      )}&limit=${limit}&page=${page}`
    ),
  getProtein: (id) => request(`/proteins/${encodeURIComponent(id)}`),
  getProteinDomains: (id) =>
    request(`/proteins/${encodeURIComponent(id)}/domains`),
  getProteinSimilar: (id) =>
    request(`/proteins/${encodeURIComponent(id)}/similar`),

  // Graph
  buildGraph: (params) =>
    request(`/graph/build?min_similarity=${params.min_similarity || 0.1}`, {
      method: "POST",
    }),
  graphNeighbors: (id, depth = 1) =>
    request(`/graph/${encodeURIComponent(id)}/neighbors?depth=${depth}`),
  graphStats: () => request("/graph/statistics"),

  // Annotation
  propagate: (body) =>
    request("/annotation/propagate", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  evaluate: (attribute) => request(`/annotation/evaluate/${attribute}`),

  // Import
  importProteins: (formData) =>
    fetch(API_BASE + "/import/proteins", { method: "POST", body: formData }),
  generateSample: (num) =>
    request(`/import/generate-sample?num_proteins=${num}`, { method: "POST" }),

  // Statistics
  databaseStats: () => request("/statistics/database"),
  graphStatistics: () => request("/statistics/graph"),
};
