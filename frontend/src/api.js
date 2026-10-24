const API = "https://trustvault-5lmo.onrender.com/api";

export function getToken() { return localStorage.getItem("trustvault_access"); }
export function setTokens(data) {
  localStorage.setItem("trustvault_access", data.access);
  localStorage.setItem("trustvault_refresh", data.refresh);
}
export function logout() {
  localStorage.removeItem("trustvault_access");
  localStorage.removeItem("trustvault_refresh");
}
export async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { const body = await response.json(); message = body.detail || JSON.stringify(body); } catch {}
    throw new Error(message);
  }
  if (response.status === 204) return null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return response.json();
  return response.blob();
}
export async function downloadDocument(id, filename) {
  const blob = await api(`/documents/${id}/download/`);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}
