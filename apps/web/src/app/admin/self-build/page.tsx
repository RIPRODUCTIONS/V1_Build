"use client";
import { useEffect, useState } from "react";

type Proposal = {
  id: number;
  template_id?: string;
  name: string;
  description?: string;
  category: string;
  score: number;
  status: string;
  created_at?: string;
};

export default function SelfBuildAdminPage() {
  const [items, setItems] = useState<Proposal[]>([]);
  const [msg, setMsg] = useState("");

  const load = async () => {
    try {
      const res = await fetch(`/api/assistant/self_build/proposals`).then((x) => x.json());
      setItems(res.items || []);
    } catch {}
  };

  useEffect(() => { load(); }, []);

  const scan = async () => {
    setMsg("");
    try {
      const res = await fetch(`/api/assistant/self_build/scan`, { method: "POST" }).then((x) => x.json());
      setMsg(`Scan ok. Proposals: ${(res.proposals||[]).length}`);
      await load();
    } catch (e: any) {
      setMsg(`Scan error: ${e?.message || e}`);
    }
  };

  const approve = async (id: number) => {
    setMsg("");
    await fetch(`/api/assistant/self_build/proposals/${id}/approve`, { method: "POST" });
    await load();
  };

  const apply = async (id: number) => {
    setMsg("");
    await fetch(`/api/assistant/self_build/proposals/${id}/apply`, { method: "POST" });
    await load();
  };

  return (
    <section className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Self-Build Proposals</h1>
        <button className="bg-blue-600 text-white px-3 py-1 rounded text-sm" onClick={scan}>Run Weekly Scan</button>
      </div>
      {msg && <div className="text-sm text-gray-700">{msg}</div>}
      <div className="border rounded p-4 bg-white">
        {!items.length && <div className="text-sm text-gray-600">No proposals yet.</div>}
        {!!items.length && (
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2 pr-4">Name</th>
                <th className="py-2 pr-4">Category</th>
                <th className="py-2 pr-4">Score</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id} className="border-b">
                  <td className="py-2 pr-4">
                    <div className="font-medium">{p.name}</div>
                    <div className="text-xs text-gray-600">{p.description}</div>
                  </td>
                  <td className="py-2 pr-4">{p.category}</td>
                  <td className="py-2 pr-4">{p.score.toFixed(2)}</td>
                  <td className="py-2 pr-4">{p.status}</td>
                  <td className="py-2 pr-4 space-x-2">
                    <button className="underline text-blue-700" onClick={() => approve(p.id)}>Approve</button>
                    <button className="underline text-green-700" onClick={() => apply(p.id)}>Apply</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}


