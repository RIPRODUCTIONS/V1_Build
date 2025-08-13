"use client";
import { useEffect, useState } from "react";

type Template = {
  id: string;
  name: string;
  description?: string;
  category: string;
};

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [category, setCategory] = useState<string>("");
  const [targets, setTargets] = useState<string>("");
  const [resp, setResp] = useState<any>(null);

  async function load() {
    const q = category ? `?category=${encodeURIComponent(category)}` : "";
    const r = await fetch(`/api/templates${q}`).then((x) => x.json());
    setTemplates(r.templates || []);
  }

  useEffect(() => {
    load();
  }, [category]);

  return (
    <section className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">Templates</h1>
      <div className="flex gap-2 items-center">
        <label className="text-sm">Category</label>
        <input className="border px-2 py-1 rounded" value={category} onChange={(e)=>setCategory(e.target.value)} placeholder="lead_generation" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {templates.map((t) => (
          <div key={t.id} className="border rounded p-3 bg-white">
            <div className="font-medium">{t.name}</div>
            <div className="text-xs text-gray-600">{t.category}</div>
            <p className="text-sm mt-1">{t.description}</p>
            {t.id === "contact_form_lead_generator" && (
              <div className="mt-2 space-y-2">
                <input className="border px-2 py-1 rounded w-full" value={targets} onChange={(e)=>setTargets(e.target.value)} placeholder="https://example.com/contact, https://httpbin.org/forms/post" />
                <button className="border px-3 py-1 rounded" onClick={async ()=>{
                  const body = {
                    target_websites: targets.split(",").map(s=>s.trim()).filter(Boolean),
                    contact_message_template: "Hello from automation",
                    sender_information: { name: "Tester", email: "test@example.com" }
                  };
                  const r = await fetch(`/api/templates/${t.id}/deploy`, { method: 'POST', headers: { 'content-type':'application/json' }, body: JSON.stringify(body)}).then(x=>x.json());
                  setResp(r);
                }}>Deploy</button>
              </div>
            )}
          </div>
        ))}
      </div>
      {resp && (
        <pre className="bg-black text-white p-3 rounded text-xs overflow-auto">{JSON.stringify(resp, null, 2)}</pre>
      )}
    </section>
  );
}


