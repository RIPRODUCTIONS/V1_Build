"use client";

import { useState } from "react";
import { components } from "@/lib/api-types";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/users/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password } satisfies components["schemas"]["LoginRequest"]),
      });
      if (!res.ok) throw new Error("Login failed");
      const data = (await res.json()) as { access_token: string };
      localStorage.setItem("token", data.access_token);
      window.location.href = "/dashboard";
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
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <button className="w-full px-4 py-2 rounded bg-blue-600 text-white">Sign In</button>
      </form>
    </main>
  );
}
