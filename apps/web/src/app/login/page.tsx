"use client";

import { useEffect, useState } from "react";
import { components } from "@/lib/api-types";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [isDesktop, setIsDesktop] = useState(false);

  useEffect(() => {
    setIsDesktop(typeof window !== "undefined" && !!(window as any).builder);
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (isDesktop && (window as any).builder?.signIn) {
        const resp = await (window as any).builder.signIn(email, password, remember);
        if (!resp?.ok) throw new Error(resp?.error || "Login failed");
        window.location.href = "/";
        return;
      }
      const body = new URLSearchParams({ username: email, password });
      const res = await fetch("/api/auth/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });
      if (!res.ok) throw new Error("Login failed");
      const data = (await res.json()) as { access_token: string };
      if (remember) localStorage.setItem("token", data.access_token);
      window.location.href = "/";
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center">
      <form onSubmit={onSubmit} className="p-8 rounded-lg bg-white shadow w-full max-w-md space-y-4">
        <h1 className="text-xl font-semibold">Login</h1>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          type="email"
          className="w-full border rounded px-3 py-2"
          placeholder="Email"
          required
        />
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          type="password"
          className="w-full border rounded px-3 py-2"
          placeholder="Password"
          required
        />
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
          Remember me
        </label>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <button className="w-full px-4 py-2 rounded bg-blue-600 text-white">Sign In</button>

        {isDesktop ? (
          <div className="pt-4 border-t mt-4 space-y-2">
            <p className="text-sm text-gray-600">Alternatively, paste your Internal API Key to authenticate desktop automations.</p>
            <input
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              type="password"
              className="w-full border rounded px-3 py-2"
              placeholder="Internal API Key"
            />
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
                Remember key
              </label>
              <button
                type="button"
                className="px-3 py-2 rounded bg-slate-800 text-white"
                onClick={async () => {
                  setError(null);
                  try {
                    const resp = await (window as any).builder.setApiKey(apiKey, remember);
                    if (!resp?.ok) throw new Error(resp?.error || "Failed to store key");
                    window.location.href = "/";
                  } catch (e: any) { setError(String(e?.message || e)); }
                }}
              >Use API Key</button>
            </div>
          </div>
        ) : null}
      </form>
    </main>
  );
}
