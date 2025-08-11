"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface ValidationResult {
  idea: any;
  trend_score: number;
  sentiment: {
    avg: number;
    n: number;
    positive_count: number;
    negative_count: number;
  };
  market_size: {
    tam: number | null;
    sam: number | null;
    notes: string;
  };
  competition: {
    count: number;
    top: Array<{ name: string; url: string }>;
    market_saturation: string;
  };
  risk: Array<{
    type: string;
    level: string;
    note: string;
  }>;
  recommended_action: string;
  explanations: Array<{
    title: string;
    detail: string;
  }>;
  validation_timestamp: string;
  correlation_id: string;
  run_id: string;
}

interface ValidationRun {
  run_id: string;
  status: string;
  created_at: string;
  correlation_id: string;
  validation_result: ValidationResult | null;
}

interface ValidationFilters {
  min_trend: number;
  min_sentiment: number;
  competition_max: number;
  action: string;
}

export default function ResearchPage() {
  const [validations, setValidations] = useState<ValidationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<ValidationFilters>({
    min_trend: 0,
    min_sentiment: -1.0,
    competition_max: 100,
    action: "",
  });
  const [currentRun, setCurrentRun] = useState<any>(null);
  const [runInput, setRunInput] = useState<{
    idea: string;
    run_id: string;
  }>({ idea: "", run_id: "" });

  useEffect(() => {
    fetchValidations();
  }, [filters]);

  const fetchValidations = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        min_trend: filters.min_trend.toString(),
        min_sentiment: filters.min_sentiment.toString(),
        competition_max: filters.competition_max.toString(),
        ...(filters.action && { action: filters.action }),
      });

      const response = await fetch(`/api/research/validations?${params}`);
      if (response.ok) {
        const data = await response.json();
        setValidations(data.validations || []);
      }
    } catch (error) {
      console.error("Failed to fetch validations:", error);
    } finally {
      setLoading(false);
    }
  };

  const runValidation = async () => {
    if (!runInput.idea && !runInput.run_id) {
      alert("Please provide either an idea or a run ID");
      return;
    }

    try {
      setCurrentRun({ status: "starting" });

      const payload: any = {};
      if (runInput.idea) {
        try {
          payload.idea = JSON.parse(runInput.idea);
        } catch {
          payload.idea = { title: runInput.idea, description: runInput.idea };
        }
      }
      if (runInput.run_id) {
        payload.run_id = runInput.run_id;
      }

      const response = await fetch("/api/research/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentRun(data);
        setRunInput({ idea: "", run_id: "" });
        // Refresh validations after a short delay
        setTimeout(fetchValidations, 2000);
      } else {
        throw new Error("Failed to start validation");
      }
    } catch (error) {
      console.error("Validation failed:", error);
      setCurrentRun({ status: "failed", error: error.message });
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case "proceed":
        return "bg-green-100 text-green-800";
      case "prototype":
        return "bg-blue-100 text-blue-800";
      case "watchlist":
        return "bg-yellow-100 text-yellow-800";
      case "drop":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case "high":
        return "text-red-600";
      case "medium":
        return "text-yellow-600";
      case "low":
        return "text-green-600";
      default:
        return "text-gray-600";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Research & Validation</h1>
          <p className="mt-2 text-gray-600">
            Validate business ideas using market research, sentiment analysis, and competitive intelligence
          </p>
        </div>

        {/* Run Validation Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Run Idea Validation</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Idea JSON (or paste idea text)
              </label>
              <textarea
                value={runInput.idea}
                onChange={(e) => setRunInput(prev => ({ ...prev, idea: e.target.value }))}
                placeholder='{"title": "AI-powered business automation", "description": "..."}'
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Or Source Run ID
              </label>
              <input
                type="text"
                value={runInput.run_id}
                onChange={(e) => setRunInput(prev => ({ ...prev, run_id: e.target.value }))}
                placeholder="UUID from Idea Engine run"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <button
            onClick={runValidation}
            disabled={currentRun?.status === "starting"}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {currentRun?.status === "starting" ? "Starting..." : "Run Validation"}
          </button>

          {currentRun && (
            <div className="mt-4 p-4 bg-gray-50 rounded-md">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  currentRun.status === "starting" ? "bg-yellow-400" :
                  currentRun.status === "started" ? "bg-blue-400" :
                  currentRun.status === "failed" ? "bg-red-400" : "bg-gray-400"
                }`} />
                <span className="text-sm font-medium">
                  Status: {currentRun.status}
                </span>
              </div>
              {currentRun.correlation_id && (
                <p className="text-sm text-gray-600 mt-1">
                  Correlation ID: {currentRun.correlation_id}
                </p>
              )}
              {currentRun.error && (
                <p className="text-sm text-red-600 mt-1">
                  Error: {currentRun.error}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>

                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Min Trend Score
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={filters.min_trend}
                  onChange={(e) => setFilters(prev => ({ ...prev, min_trend: parseInt(e.target.value) || 0 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  aria-label="Minimum trend score filter"
                  title="Minimum trend score filter"
                  placeholder="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Min Sentiment
                </label>
                <input
                  type="number"
                  min="-1"
                  max="1"
                  step="0.1"
                  value={filters.min_sentiment}
                  onChange={(e) => setFilters(prev => ({ ...prev, min_sentiment: parseFloat(e.target.value) || -1 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  aria-label="Minimum sentiment filter"
                  title="Minimum sentiment filter"
                  placeholder="-1.0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Competition
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={filters.competition_max}
                  onChange={(e) => setFilters(prev => ({ ...prev, competition_max: parseInt(e.target.value) || 100 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  aria-label="Maximum competition filter"
                  title="Maximum competition filter"
                  placeholder="100"
                />
              </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Action
              </label>
              <select
                value={filters.action}
                onChange={(e) => setFilters(prev => ({ ...prev, action: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Select action filter"
                title="Select action filter"
              >
                <option value="">All Actions</option>
                <option value="proceed">Proceed</option>
                <option value="prototype">Prototype</option>
                <option value="watchlist">Watchlist</option>
                <option value="drop">Drop</option>
              </select>
            </div>
          </div>
        </div>

        {/* Validations Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Idea Validations ({validations.length})
            </h2>
          </div>

          {loading ? (
            <div className="p-6 text-center text-gray-500">Loading validations...</div>
          ) : validations.length === 0 ? (
            <div className="p-6 text-center text-gray-500">No validations found</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Idea
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Trend Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sentiment
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Competition
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Action
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Details
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {validations.map((validation) => (
                    <tr key={validation.run_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {validation.validation_result?.idea?.title || "Unknown Idea"}
                        </div>
                        <div className="text-sm text-gray-500">
                          {validation.validation_result?.idea?.description || "No description"}
                        </div>
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {validation.validation_result?.trend_score || 0}/100
                        </div>
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {validation.validation_result?.sentiment?.avg?.toFixed(2) || "0.00"}
                        </div>
                        <div className="text-xs text-gray-500">
                          ({validation.validation_result?.sentiment?.n || 0} samples)
                        </div>
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {validation.validation_result?.competition?.count || 0}
                        </div>
                        <div className="text-xs text-gray-500">
                          {validation.validation_result?.competition?.market_saturation || "unknown"}
                        </div>
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getActionColor(validation.validation_result?.recommended_action || "")}`}>
                          {validation.validation_result?.recommended_action || "unknown"}
                        </span>
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(validation.created_at).toLocaleDateString()}
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <Link
                          href={`/runs/${validation.run_id}`}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          View Run
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="mt-8 flex space-x-4">
          <Link
            href="/business"
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            ← Back to Business
          </Link>

          <Link
            href="/runs"
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            View All Runs
          </Link>
        </div>
      </div>
    </div>
  );
}
