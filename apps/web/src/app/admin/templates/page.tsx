"use client";
import { useEffect, useState } from "react";

type Template = {
  id: string;
  name: string;
  description?: string;
  category: string;
  difficulty?: string;
  estimated_time_minutes?: number;
};

export default function AdminTemplatesPage() {
  const [items, setItems] = useState<Template[]>([]);
  const [ciToken, setCiToken] = useState<string>("");
  const [editing, setEditing] = useState<Template>({ id: "", name: "", category: "lead_generation" });
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

  async function load() {
    const res = await fetch(`${API_BASE}/admin/templates`, { headers: { "X-CI-Token": ciToken } });
    if (res.ok) setItems(await res.json());
  }

  useEffect(() => {
    if (ciToken) load();
  }, [ciToken]);

  async function upsert() {
    const r = await fetch(`${API_BASE}/admin/templates`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CI-Token": ciToken },
      body: JSON.stringify(editing),
    });
    if (r.ok) {
      setEditing({ id: "", name: "", category: "lead_generation" });
      load();
    }
  }

  async function del(id: string) {
    const r = await fetch(`${API_BASE}/admin/templates/${id}`, { method: "DELETE", headers: { "X-CI-Token": ciToken } });
    if (r.ok) load();
  }

  return (
    <section className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">Admin · Templates</h1>
      <div className="flex gap-2 items-center">
        <label className="text-sm">X-CI-Token</label>
        <input className="border px-2 py-1 rounded w-96" value={ciToken} onChange={(e)=>setCiToken(e.target.value)} placeholder="paste CI token" />
        <button className="border px-3 py-1 rounded" onClick={load} disabled={!ciToken}>Refresh</button>
      </div>

      <div className="border rounded p-3 bg-white space-y-2 max-w-2xl">
        <div className="font-medium">Create / Update</div>
        <div className="grid grid-cols-2 gap-2">
          <input className="border px-2 py-1 rounded" placeholder="id" value={editing.id} onChange={(e)=>setEditing({ ...editing, id: e.target.value })} />
          <input className="border px-2 py-1 rounded" placeholder="name" value={editing.name} onChange={(e)=>setEditing({ ...editing, name: e.target.value })} />
          <input className="border px-2 py-1 rounded" placeholder="category" value={editing.category} onChange={(e)=>setEditing({ ...editing, category: e.target.value })} />
          <input className="border px-2 py-1 rounded" placeholder="difficulty" value={editing.difficulty || ""} onChange={(e)=>setEditing({ ...editing, difficulty: e.target.value })} />
          <input className="border px-2 py-1 rounded col-span-2" placeholder="description" value={editing.description || ""} onChange={(e)=>setEditing({ ...editing, description: e.target.value })} />
          <input type="number" className="border px-2 py-1 rounded" placeholder="estimated minutes" value={editing.estimated_time_minutes || 0} onChange={(e)=>setEditing({ ...editing, estimated_time_minutes: Number(e.target.value) })} />
        </div>
        <button className="border px-3 py-1 rounded" onClick={upsert} disabled={!ciToken || !editing.id || !editing.name}>Save</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {items.map((t) => (
          <div key={t.id} className="border rounded p-3 bg-white">
            <div className="flex justify-between items-center">
              <div>
                <div className="font-medium">{t.name}</div>
                <div className="text-xs text-gray-600">{t.id} · {t.category} · {t.difficulty || ""}</div>
              </div>
              <button className="text-red-600 text-sm" onClick={()=>del(t.id)}>Delete</button>
            </div>
            <p className="text-sm mt-1">{t.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}


