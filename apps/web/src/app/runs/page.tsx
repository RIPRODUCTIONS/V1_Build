"use client";
import React from "react";
import { apiFetch } from "@/lib/api";

type Run = {
  run_id: string;
  status: string;
  intent: string;
  department: string;
  correlation_id: string;
  created_at: string;
};

type ManagerHealth = "healthy" | "degraded" | "down";

export default function RunsPage() {
  const [items, setItems] = React.useState<Run[]>([]);
  const [status, setStatus] = React.useState<string>("");
  const [intent, setIntent] = React.useState<string>("");
  const [department, setDepartment] = React.useState<string>("");
  const [correlationId, setCorrelationId] = React.useState<string>("");
  const [loading, setLoading] = React.useState(false);
  const [sortBy, setSortBy] = React.useState<string>("created_desc");
  const [managerHealth, setManagerHealth] = React.useState<ManagerHealth>("down");

  async function load() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      if (intent) params.set("intent", intent);
      if (department) params.set("department", department);
      if (correlationId) params.set("correlation_id", correlationId);
      params.set("sort", sortBy);
      params.set("limit", "50");
      params.set("offset", "0");

      const res = await apiFetch<{ items: Run[] }>(`/runs/?${params.toString()}`);
      setItems(res.items || []);
    } catch (error) {
      console.error("Failed to load runs:", error);
    } finally {
      setLoading(false);
    }
  }

  async function checkManagerHealth() {
    try {
      const response = await fetch("http://localhost:8080/health");
      if (response.ok) {
        setManagerHealth("healthy");
      } else {
        setManagerHealth("degraded");
      }
    } catch (error) {
      setManagerHealth("down");
    }
  }

  React.useEffect(() => {
    load();
    checkManagerHealth();

    // Set up live polling every 10 seconds
    const interval = setInterval(() => {
      load();
      checkManagerHealth();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const clearFilters = () => {
    setStatus("");
    setIntent("");
    setDepartment("");
    setCorrelationId("");
    setSortBy("created_desc");
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
    console.log(`${label} copied to clipboard`);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed": return "bg-green-100 text-green-800";
      case "started": return "bg-blue-100 text-blue-800";
      case "failed": return "bg-red-100 text-red-800";
      case "pending": return "bg-yellow-100 text-yellow-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getManagerHealthColor = (health: ManagerHealth) => {
    switch (health) {
      case "healthy": return "bg-green-100 text-green-800";
      case "degraded": return "bg-yellow-100 text-yellow-800";
      case "down": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <section className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Automation Runs</h1>
        <div className="flex items-center gap-4">
          {/* Manager Health Chip */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Manager:</span>
            <span className={`px-2 py-1 text-xs rounded-full font-medium ${getManagerHealthColor(managerHealth)}`}>
              {managerHealth === "healthy" ? "OK" : managerHealth === "degraded" ? "Degraded" : "Down"}
            </span>
          </div>
          <div className="text-sm text-gray-600">
            {items.length} run{items.length !== 1 ? 's' : ''} found
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border shadow-sm">
        <h2 className="text-lg font-medium mb-4">Filters & Sorting</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              aria-label="Filter by status"
              title="Filter by status"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="started">Started</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Intent</label>
            <input
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder="health.wellness_daily"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
            <select
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              aria-label="Filter by department"
              title="Filter by department"
            >
              <option value="">All Departments</option>
              <option value="life">Life</option>
              <option value="finance">Finance</option>
              <option value="safety">Safety</option>
              <option value="business">Business</option>
              <option value="research">Research</option>
              <option value="engineering">Engineering</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Correlation ID</label>
            <input
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={correlationId}
              onChange={(e) => setCorrelationId(e.target.value)}
              placeholder="corr_123..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
            <select
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              aria-label="Sort results by"
              title="Sort results by"
            >
              <option value="created_desc">Newest First</option>
              <option value="created_asc">Oldest First</option>
              <option value="status">By Status</option>
              <option value="intent">By Intent</option>
            </select>
          </div>
        </div>

        <div className="flex gap-3 mt-4">
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            onClick={load}
            disabled={loading}
          >
            {loading ? "Loading…" : "Apply Filters"}
          </button>
          <button
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
            onClick={clearFilters}
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        {items.length === 0 ? (
          <div className="p-8 text-center text-gray-600">
            {loading ? "Loading runs..." : "No runs found matching your filters."}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Run ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Intent</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Correlation ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {items.map((run) => (
                  <tr key={run.run_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        className="font-mono text-sm text-blue-600 hover:text-blue-800 underline"
                        onClick={() => copyToClipboard(run.run_id, "Run ID")}
                        title="Copy run ID"
                      >
                        {run.run_id.slice(0, 8)}...
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(run.status)}`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {run.intent !== "N/A" ? run.intent : "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {run.department !== "N/A" ? run.department : "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {run.correlation_id !== "N/A" ? (
                        <button
                          className="font-mono text-xs text-gray-600 hover:text-gray-800 underline"
                          onClick={() => copyToClipboard(run.correlation_id, "Correlation ID")}
                          title="Copy correlation ID"
                        >
                          {run.correlation_id.slice(0, 8)}...
                        </button>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(run.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
