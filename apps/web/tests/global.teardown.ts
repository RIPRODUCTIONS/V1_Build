import fetch from "node-fetch";
const API = process.env.API_BASE_URL || "http://127.0.0.1:8000";
const TOKEN = process.env.CI_CLEANUP_TOKEN || "";

export default async function globalTeardown() {
  if (!TOKEN) return;
  await fetch(`${API}/admin/cleanup/all`, {
    method: "DELETE",
    headers: { "X-CI-Token": TOKEN },
  }).catch(() => {});
}
