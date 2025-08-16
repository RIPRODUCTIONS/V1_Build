"use client";

import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8001";
const API_KEY = "dev-key";

export default function InventoryPage() {
  const [jsonReport, setJsonReport] = useState<any>(null);
  const [markdownReport, setMarkdownReport] = useState<string>("");
  const [diagram, setDiagram] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const headers = { "X-API-Key": API_KEY } as Record<string, string>;
    Promise.all([
      fetch(`${API_BASE}/api/diagnostics`, { headers }).then((r) => r.json()),
      fetch(`${API_BASE}/api/diagnostics/report`, { headers }).then((r) =>
        r.text(),
      ),
      fetch(`${API_BASE}/api/diagnostics/diagram`, { headers }).then((r) =>
        r.text(),
      ),
    ])
      .then(([jsonData, md, mermaid]) => {
        setJsonReport(jsonData);
        setMarkdownReport(md);
        setDiagram(mermaid);
      })
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">System Inventory</h1>
      {error && <div className="text-red-600">Error: {error}</div>}

      <section>
        <h2 className="text-xl font-semibold mb-2">
          Architecture Diagram (Mermaid)
        </h2>
        <pre className="bg-gray-900 text-green-200 p-4 rounded whitespace-pre-wrap overflow-auto">
          {diagram}
        </pre>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-2">Markdown Report</h2>
        <pre className="bg-gray-100 p-4 rounded whitespace-pre-wrap overflow-auto">
          {markdownReport}
        </pre>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-2">JSON Diagnostics</h2>
        <pre className="bg-gray-100 p-4 rounded whitespace-pre-wrap overflow-auto text-xs">
          {JSON.stringify(jsonReport, null, 2)}
        </pre>
      </section>
    </div>
  );
}


