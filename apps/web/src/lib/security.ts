export function buildAuthHeaders(): HeadersInit {
  const apiKey = process.env.NEXT_PUBLIC_INTERNAL_API_KEY || "";
  return apiKey ? { "X-API-Key": apiKey } : {};
}

export function sseUrl(url: string): string {
  const apiKey = process.env.NEXT_PUBLIC_INTERNAL_API_KEY || "";
  if (!apiKey) return url;
  const u = new URL(url, typeof window !== 'undefined' ? window.location.origin : 'http://localhost');
  u.searchParams.set('token', apiKey);
  return u.toString();
}


