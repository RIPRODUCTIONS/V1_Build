"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Run = {
  run_id: string;
  status: string;
  intent: string;
  department: string;
  correlation_id: string;
  created_at: string;
};

type ManagerHealth = "healthy" | "degraded" | "down";

export default function RunsConsole() {
  const router = useRouter();
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [managerHealth, setManagerHealth] = useState<ManagerHealth>("down");
  const [filters, setFilters] = useState({
    status: "",
    department: "",
    intent: "",
    correlation_id: "",
  });
  const [pagination, setPagination] = useState({
    limit: 50,
    offset: 0,
    sort: "created_desc" as "created_desc" | "created_asc" | "status" | "intent",
  });

  // Fetch runs with current filters and pagination
  const fetchRuns = async () => {
    try {
      const params = new URLSearchParams({
        limit: pagination.limit.toString(),
        offset: pagination.offset.toString(),
        sort: pagination.sort,
        ...(filters.status && { status: filters.status }),
        ...(filters.department && { department: filters.department }),
        ...(filters.intent && { intent: filters.intent }),
        ...(filters.correlation_id && { correlation_id: filters.correlation_id }),
      });

      const response = await fetch(`/api/runs?${params}`);
      if (response.ok) {
        const data = await response.json();
        setRuns(data.items || []);
      }
    } catch (error) {
      console.error("Failed to fetch runs:", error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch manager health
  const fetchManagerHealth = async () => {
    try {
      const response = await fetch("/api/health/manager");
      if (response.ok) {
        const data = await response.json();
        setManagerHealth(data.status === "healthy" ? "healthy" : "degraded");
      } else {
        setManagerHealth("down");
      }
    } catch (error) {
      setManagerHealth("down");
    }
  };

  // Initial load
  useEffect(() => {
    fetchRuns();
    fetchManagerHealth();
  }, [filters, pagination]);

  // Poll for updates every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchRuns();
      fetchManagerHealth();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  // Handle filter changes
  const handleFilterChange = (key: keyof typeof filters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, offset: 0 })); // Reset to first page
  };

  // Handle pagination
  const handlePageChange = (newOffset: number) => {
    setPagination(prev => ({ ...prev, offset: newOffset }));
  };

  // Handle sorting
  const handleSortChange = (newSort: typeof pagination.sort) => {
    setPagination(prev => ({ ...prev, sort: newSort, offset: 0 }));
  };

  // Copy correlation ID to clipboard
  const copyCorrelationId = (correlationId: string) => {
    navigator.clipboard.writeText(correlationId);
    // Could add a toast notification here
  };

  // Cancel run (if pending/started)
  const cancelRun = async (runId: string) => {
    try {
      const response = await fetch(`/api/runs/${runId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "cancelled" }),
      });

      if (response.ok) {
        // Refresh the runs list
        fetchRuns();
      }
    } catch (error) {
      console.error("Failed to cancel run:", error);
    }
  };

  // View artifacts
  const viewArtifacts = (runId: string) => {
    router.push(`/runs/${runId}/artifacts`);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
      case "succeeded":
        return "bg-green-100 text-green-800";
      case "failed":
      case "error":
        return "bg-red-100 text-red-800";
      case "started":
      case "running":
        return "bg-blue-100 text-blue-800";
      case "pending":
      case "queued":
        return "bg-yellow-100 text-yellow-800";
      case "cancelled":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getManagerHealthColor = (health: ManagerHealth) => {
    switch (health) {
      case "healthy":
        return "bg-green-100 text-green-800";
      case "degraded":
        return "bg-yellow-100 text-yellow-800";
      case "down":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Runs Console</h1>
              <p className="mt-2 text-gray-600">
                Monitor and manage automation runs across all departments
              </p>
            </div>

            {/* Manager Health Chip */}
            <div className="flex items-center space-x-4">
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${getManagerHealthColor(managerHealth)}`}>
                Manager: {managerHealth}
              </div>
              <button
                onClick={() => fetchManagerHealth()}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters & Search</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange("status", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Filter by status"
                title="Filter by status"
              >
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="started">Started</option>
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="succeeded">Succeeded</option>
                <option value="failed">Failed</option>
                <option value="error">Error</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Department
              </label>
              <select
                value={filters.department}
                onChange={(e) => handleFilterChange("department", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Filter by department"
                title="Filter by department"
              >
                <option value="">All Departments</option>
                <option value="business">Business</option>
                <option value="research">Research</option>
                <option value="engineering">Engineering</option>
                <option value="finance">Finance</option>
                <option value="life">Life</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Intent
              </label>
              <input
                type="text"
                value={filters.intent}
                onChange={(e) => handleFilterChange("intent", e.target.value)}
                placeholder="e.g., ideation.generate"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Correlation ID
              </label>
              <input
                type="text"
                value={filters.correlation_id}
                onChange={(e) => handleFilterChange("correlation_id", e.target.value)}
                placeholder="Search by correlation ID"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Sort Options */}
          <div className="mt-4 flex items-center space-x-4">
            <span className="text-sm font-medium text-gray-700">Sort by:</span>
            <select
              value={pagination.sort}
              onChange={(e) => handleSortChange(e.target.value as typeof pagination.sort)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Sort results by"
              title="Sort results by"
            >
              <option value="created_desc">Newest First</option>
              <option value="created_asc">Oldest First</option>
              <option value="status">Status</option>
              <option value="intent">Intent</option>
            </select>
          </div>
        </div>

        {/* Runs Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Automation Runs ({runs.length})
            </h3>
          </div>

          {loading ? (
            <div className="p-8 text-center">
              <div className="text-gray-500">Loading runs...</div>
            </div>
          ) : runs.length === 0 ? (
            <div className="p-8 text-center">
              <div className="text-gray-500">No runs found matching your filters.</div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Run ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Intent
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Department
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Correlation ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {runs.map((run) => (
                    <tr key={run.run_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                        {run.run_id.slice(0, 8)}...
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(run.status)}`}>
                          {run.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {run.intent}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {run.department}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                        {run.correlation_id.slice(0, 8)}...
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(run.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => copyCorrelationId(run.correlation_id)}
                            className="text-blue-600 hover:text-blue-800"
                            title="Copy Correlation ID"
                          >
                            📋
                          </button>

                          <button
                            onClick={() => viewArtifacts(run.run_id)}
                            className="text-green-600 hover:text-green-800"
                            title="View Artifacts"
                          >
                            📁
                          </button>

                          {(run.status === "pending" || run.status === "started") && (
                            <button
                              onClick={() => cancelRun(run.run_id)}
                              className="text-red-600 hover:text-red-800"
                              title="Cancel Run"
                            >
                              ❌
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {runs.length > 0 && (
            <div className="px-6 py-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Showing {pagination.offset + 1} to {pagination.offset + runs.length} of results
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handlePageChange(Math.max(0, pagination.offset - pagination.limit))}
                    disabled={pagination.offset === 0}
                    className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => handlePageChange(pagination.offset + pagination.limit)}
                    disabled={runs.length < pagination.limit}
                    className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="flex space-x-4">
            <button
              onClick={() => router.push("/business")}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Launch Idea Engine
            </button>
            <button
              onClick={() => router.push("/research/market-gaps")}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
            >
              Run Market Gap Scanner
            </button>
            <button
              onClick={() => fetchRuns()}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            >
              Refresh Runs
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
