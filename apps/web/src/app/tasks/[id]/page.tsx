"use client";

import { useEffect, useState } from "react";
import ConfirmDialog from "@/components/ConfirmDialog";
import { components } from "@/lib/api-types";
import { useRouter } from "next/navigation";

type TaskOut = components["schemas"]["TaskOut"];
type TaskUpdate = components["schemas"]["TaskUpdate"];

export default function TaskDetail({ params }: { params: { id: string } }) {
  const id = Number(params.id);
  const router = useRouter();
  const [task, setTask] = useState<TaskOut | null>(null);
  const [form, setForm] = useState<TaskUpdate>({ title: undefined, status: undefined, lead_id: undefined });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.replace("/login");
      return;
    }
    async function load() {
      try {
        const res = await fetch("http://127.0.0.1:8000/tasks/", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("Failed to load task");
        const list = (await res.json()) as TaskOut[];
        const item = list.find((t) => t.id === id) || null;
        setTask(item);
        if (item) setForm({ title: item.title, status: item.status, lead_id: item.lead_id ?? undefined });
      } catch (e: any) {
        setError(e.message);
      }
    }
    void load();
  }, [id, router]);

  async function onSave() {
    const token = localStorage.getItem("token");
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/tasks/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(form satisfies TaskUpdate),
      });
      if (!res.ok) throw new Error("Failed to update task");
      const updated = (await res.json()) as TaskOut;
      setTask(updated);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function onDelete() {
    const token = localStorage.getItem("token");
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/tasks/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to delete task");
      router.replace("/dashboard");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
      setConfirmOpen(false);
    }
  }

  if (!task) return <main className="p-6">{error ? <p className="text-red-600">{error}</p> : "Loading..."}</main>;

  return (
    <main className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Edit Task</h1>
      {error && <p className="text-red-600">{error}</p>}
      <div className="grid gap-3 max-w-lg">
        <input
          className="border rounded px-3 py-2"
          value={form.title ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          placeholder="Title"
        />
        <input
          className="border rounded px-3 py-2"
          value={form.status ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
          placeholder="Status"
        />
        <div className="flex gap-3">
          <button onClick={onSave} disabled={loading} className="px-4 py-2 rounded bg-blue-600 text-white">
            {loading ? "Saving..." : "Save"}
          </button>
          <button onClick={() => setConfirmOpen(true)} className="px-4 py-2 rounded bg-red-600 text-white">
            Delete
          </button>
        </div>
      </div>
      <ConfirmDialog
        open={confirmOpen}
        title="Delete Task"
        message="Are you sure you want to delete this task? This action cannot be undone."
        onCancel={() => setConfirmOpen(false)}
        onConfirm={onDelete}
      />
    </main>
  );
}
