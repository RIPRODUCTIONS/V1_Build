"use client";
import React, { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";

type MarketGap = {
  id: string;
  title: string;
  description: string;
  opportunity_score: number;
  market_size: string;
  competition_level: string;
  sources: string[];
  created_at: string;
};

type ResearchRun = {
  run_id: string;
  status: string;
  created_at: string;
  correlation_id: string;
  artifacts: Array<{
    id: number;
    kind: string;
    status: string;
    file_path: string;
  }>;
};

export default function MarketGapsPage() {
  const [marketGaps, setMarketGaps] = useState<MarketGap[]>([]);
  const [recentRuns, setRecentRuns] = useState<ResearchRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [gapsRes, runsRes] = await Promise.all([
        apiFetch<{ market_gaps: MarketGap[] }>("/research/market-gaps/latest"),
        apiFetch<{ results: ResearchRun[] }>("/research/market-gaps/results")
      ]);

      setMarketGaps(gapsRes?.market_gaps || []);
      setRecentRuns(runsRes?.results || []);
    } catch (error) {
      console.error("Failed to load research data:", error);
    }
  };

  const runScanner = async () => {
    setScanning(true);
    try {
      const res = await apiFetch<{ run_id: string; message: string }>("/research/market-gaps/run", {
        method: "POST",
        body: JSON.stringify({}),
      });

      console.log("Scanner started:", res.message);

      // Poll for updates
      setTimeout(() => {
        loadData();
        setScanning(false);
      }, 2000);

    } catch (error) {
      console.error("Failed to start scanner:", error);
      setScanning(false);
    }
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

  const getOpportunityColor = (score: number) => {
    if (score >= 8) return "text-green-600 font-semibold";
    if (score >= 6) return "text-yellow-600 font-semibold";
    return "text-red-600 font-semibold";
  };

  return (
    <section className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Research Department</h1>
          <p className="text-gray-600 mt-2">Market analysis and opportunity identification</p>
        </div>
        <button
          onClick={runScanner}
          disabled={scanning}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {scanning ? "Scanning..." : "Run Market Gap Scanner"}
        </button>
      </div>

      {/* Market Gaps */}
      <div className="bg-white rounded-lg border shadow-sm">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Latest Market Gaps</h2>
          <p className="text-gray-600 text-sm mt-1">
            Top business opportunities identified by AI analysis
          </p>
        </div>

        {marketGaps.length === 0 ? (
          <div className="p-8 text-center text-gray-600">
            No market gaps found. Run the scanner to identify opportunities.
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {marketGaps.map((gap, index) => (
              <div key={gap.id || index} className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {gap.title}
                    </h3>
                    <p className="text-gray-600 mb-3">{gap.description}</p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-gray-700">Opportunity Score:</span>
                        <span className={`ml-2 ${getOpportunityColor(gap.opportunity_score)}`}>
                          {gap.opportunity_score}/10
                        </span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Market Size:</span>
                        <span className="ml-2 text-gray-600">{gap.market_size}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Competition:</span>
                        <span className="ml-2 text-gray-600">{gap.competition_level}</span>
                      </div>
                    </div>

                    {gap.sources && gap.sources.length > 0 && (
                      <div className="mt-3">
                        <span className="font-medium text-gray-700 text-sm">Sources:</span>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {gap.sources.map((source, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                            >
                              {source}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Runs */}
      <div className="bg-white rounded-lg border shadow-sm">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Recent Scans</h2>
          <p className="text-gray-600 text-sm mt-1">
            History of market gap scanner runs
          </p>
        </div>

        {recentRuns.length === 0 ? (
          <div className="p-8 text-center text-gray-600">
            No recent scans found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Run ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Correlation ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Artifacts
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {recentRuns.map((run) => (
                  <tr key={run.run_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-blue-600">
                      {run.run_id.slice(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(run.status)}`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(run.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-600">
                      {run.correlation_id.slice(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {run.artifacts.length} artifact{run.artifacts.length !== 1 ? 's' : ''}
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
