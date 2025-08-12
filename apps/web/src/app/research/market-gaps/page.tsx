'use client';
import { useEffect, useState } from 'react';

type MarketGapReport = {
  scan_timestamp: string;
  industry_focus: string;
  market_size: string;
  geographic_scope: string;
  trends_analyzed: number;
  gaps_identified: number;
  opportunities_scored: number;
  top_opportunities: Array<{
    gap_type: string;
    description: string;
    trend: string;
    urgency: string;
    estimated_tam: number;
    barriers_to_entry: string;
    time_to_market: string;
    opportunity_score: number;
  }>;
  competitive_landscape: {
    analysis_timestamp: string;
    opportunities_analyzed: number;
    competitive_insights: Array<{
      opportunity: string;
      competitors: Array<{
        name: string;
        size: string;
        market_share: string;
        threat_level: string;
      }>;
      market_positioning: {
        positioning_strategy: string;
        target_segment: string;
        value_proposition: string;
      };
      entry_strategies: string[];
    }>;
  };
  execution_time: number;
};

type Run = {
  run_id: string;
  status: string;
  intent: string;
  department: string;
  correlation_id: string;
  created_at: string;
  artifacts?: Array<{
    id: string;
    kind: string;
    status: string;
    file_path: string;
  }>;
};

export default function MarketGapScanner() {
  const [loading, setLoading] = useState(false);
  const [currentRun, setCurrentRun] = useState<string | null>(null);
  const [runs, setRuns] = useState<Record<string, Run>>({});
  const [latestReport, setLatestReport] = useState<MarketGapReport | null>(null);
  const [scanning, setScanning] = useState(false);
  type Gap = {
    id?: string;
    title: string;
    description: string;
    opportunity_score: number;
    market_size: string;
    competition_level: string;
    sources?: string[];
  };
  type RecentRun = {
    run_id: string;
    status: string;
    created_at: string;
    correlation_id: string;
    artifacts: unknown[];
  };
  const [marketGaps, _setMarketGaps] = useState<Gap[]>([]);
  const [recentRuns, _setRecentRuns] = useState<RecentRun[]>([]);
  const [scanParams, setScanParams] = useState({
    industry_focus: 'technology',
    market_size: 'all',
    geographic_scope: 'global',
  });

  // Fetch latest market gap results
  const fetchLatestResults = async () => {
    try {
      const response = await fetch('/api/research/market-gaps/latest');
      if (response.ok) {
        const data = await response.json();
        if (data.latest_report) {
          setLatestReport(data.latest_report);
        }
      }
    } catch (error) {
      console.error('Failed to fetch latest results:', error);
    }
  };

  // Fetch recent runs
  const fetchRecentRuns = async () => {
    try {
      const response = await fetch('/api/research/market-gaps/results');
      if (response.ok) {
        const data = await response.json();
        const runsMap: Record<string, Run> = {};
        data.results.forEach((run: Run) => {
          runsMap[run.run_id] = run;
        });
        setRuns(runsMap);
      }
    } catch (error) {
      console.error('Failed to fetch recent runs:', error);
    }
  };

  // Initial load
  useEffect(() => {
    fetchLatestResults();
    fetchRecentRuns();
  }, []);

  // Poll for updates
  useEffect(() => {
    const interval = setInterval(() => {
      if (currentRun) {
        fetchRecentRuns();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [currentRun]);

  // Run market gap scanner
  const runScanner = async () => {
    setLoading(true);
    setScanning(true);
    try {
      const response = await fetch('/api/research/market-gaps/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(scanParams),
      });

      if (response.ok) {
        const result = await response.json();
        setCurrentRun(result.run_id);
        setRuns(prev => ({
          ...prev,
          [result.run_id]: {
            run_id: result.run_id,
            status: 'started',
            intent: result.intent,
            department: result.department,
            correlation_id: result.correlation_id,
            created_at: new Date().toISOString(),
          },
        }));
      }
    } catch (error) {
      console.error('Failed to run scanner:', error);
    } finally {
      setLoading(false);
      setScanning(false);
    }
  };

  const _formatTAM = (tam: number) => {
    if (tam >= 1000000000) {
      return `$${(tam / 1000000000).toFixed(1)}B`;
    } else if (tam >= 1000000) {
      return `$${(tam / 1000000).toFixed(1)}M`;
    } else {
      return `$${(tam / 1000).toFixed(1)}K`;
    }
  };

  const _getUrgencyColor = (urgency: string) => {
    switch (urgency.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  const _getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getOpportunityColor = (score: number) =>
    score >= 8 ? 'text-green-600' : score >= 5 ? 'text-yellow-600' : 'text-red-600';

  const getStatusColor = (status: string) =>
    status === 'succeeded'
      ? 'bg-green-100 text-green-800'
      : status === 'failed'
        ? 'bg-red-100 text-red-800'
        : status === 'running'
          ? 'bg-blue-100 text-blue-800'
          : 'bg-gray-100 text-gray-800';

  return (
    <section className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Market Gap Scanner</h1>
          <p className="mt-2 text-gray-600">
            AI-powered market research to identify business opportunities and competitive gaps
          </p>
        </div>

        {/* Scanner Controls */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Scanner Configuration</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Industry Focus</label>
              <select
                value={scanParams.industry_focus}
                onChange={e => setScanParams(prev => ({ ...prev, industry_focus: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Select industry focus"
                title="Select industry focus"
              >
                <option value="all">All Industries</option>
                <option value="technology">Technology</option>
                <option value="healthcare">Healthcare</option>
                <option value="finance">Finance</option>
                <option value="retail">Retail</option>
                <option value="manufacturing">Manufacturing</option>
                <option value="education">Education</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Market Size</label>
              <select
                value={scanParams.market_size}
                onChange={e => setScanParams(prev => ({ ...prev, market_size: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Select market size"
                title="Select market size"
              >
                <option value="all">All Sizes</option>
                <option value="small">Small Business</option>
                <option value="medium">Medium Business</option>
                <option value="large">Large Enterprise</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Geographic Scope
              </label>
              <select
                value={scanParams.geographic_scope}
                onChange={e =>
                  setScanParams(prev => ({ ...prev, geographic_scope: e.target.value }))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Select geographic scope"
                title="Select geographic scope"
              >
                <option value="global">Global</option>
                <option value="regional">Regional</option>
                <option value="local">Local</option>
              </select>
            </div>
          </div>

          <button
            onClick={runScanner}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Scanning...' : 'Run Market Gap Scanner'}
          </button>
        </div>

        {/* Active Runs */}
        {currentRun && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Active Scan</h2>
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <div className="text-sm text-gray-600">Run ID: {currentRun}</div>
                <div className="text-sm text-gray-600">
                  Status: <span className="font-medium">{runs[currentRun]?.status}</span>
                </div>
                <div className="text-sm text-gray-600">
                  Started:{' '}
                  {runs[currentRun]?.created_at
                    ? new Date(runs[currentRun].created_at).toLocaleString()
                    : 'N/A'}
                </div>
              </div>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          </div>
        )}

        {/* Latest Results */}
        {latestReport && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Latest Market Gap Report</h2>

            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {latestReport.trends_analyzed}
                </div>
                <div className="text-sm text-gray-600">Trends Analyzed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {latestReport.gaps_identified}
                </div>
                <div className="text-sm text-gray-600">Gaps Identified</div>
              </div>
            </div>
          </div>
        )}

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
            {scanning ? 'Scanning...' : 'Run Market Gap Scanner'}
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
                      <h3 className="text-lg font-medium text-gray-900 mb-2">{gap.title}</h3>
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
            <p className="text-gray-600 text-sm mt-1">History of market gap scanner runs</p>
          </div>

          {recentRuns.length === 0 ? (
            <div className="p-8 text-center text-gray-600">No recent scans found.</div>
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
                  {recentRuns.map(run => (
                    <tr key={run.run_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-blue-600">
                        {run.run_id.slice(0, 8)}...
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(run.status)}`}
                        >
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
      </div>
    </section>
  );
}
