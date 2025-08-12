'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';

import RecentRunsPanel from '@/components/RecentRunsPanel';
import { copyToClipboard, generateCurl, getRun, pollRun, submit } from '@/lib/automation';

interface ValidationResult {
  idea: {
    title: string;
    description: string;
    market_size: string;
    complexity: string;
  };
  trend_score: number;
  sentiment: {
    avg: number;
    n: number;
    positive_count: number;
    negative_count: number;
  };
  market_size: {
    tam: number;
    sam: number;
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

export default function ResearchPage() {
  const [validations, setValidations] = useState<ValidationResult[]>([]);
  const [currentRun, setCurrentRun] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [ideaInput, setIdeaInput] = useState('');
  const [sourceRunId, setSourceRunId] = useState('');
  const [filterTrend, setFilterTrend] = useState('');
  const [filterSentiment, setFilterSentiment] = useState('');
  const [filterCompetition, setFilterCompetition] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const searchParams = useSearchParams();

  useEffect(() => {
    // Load recent validations
    fetchValidations();
  }, []);

  // Deep-link consumption: load run from URL if present
  useEffect(() => {
    const runId = searchParams.get('runId');
    if (!runId) return;

    let cancelled = false;
    (async () => {
      try {
        const run = await getRun(runId);
        if (
          !cancelled &&
          run.status === 'succeeded' &&
          run.detail?.intent === 'research.validate_idea'
        ) {
          // Refresh validations to show the new result
          fetchValidations();
        }
      } catch (error) {
        console.error('Failed to load run from deep-link:', error);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [searchParams]);

  const fetchValidations = async () => {
    try {
      // Get recent runs and filter for research validation results
      const response = await fetch('/automation/recent');
      if (response.ok) {
        const data = (await response.json()) as {
          items: Array<{ status?: string; detail?: { intent?: string; result?: unknown } }>;
        };
        // Filter for research validation runs
        const researchRuns = data.items.filter(
          run => run.detail?.intent === 'research.validate_idea' && run.status === 'succeeded',
        );

        // Transform runs to validation results
        const validationResults = researchRuns
          .map(run => {
            const result = run.detail?.result as { validation_result?: ValidationResult } | null;
            if (result?.validation_result) {
              return result.validation_result as ValidationResult;
            }
            return null;
          })
          .filter(Boolean) as ValidationResult[];

        setValidations(validationResults);
      }
    } catch (error) {
      console.error('Failed to fetch validations:', error);
    }
  };

  const runValidation = async () => {
    if (!ideaInput.trim() && !sourceRunId.trim()) {
      alert('Please provide either an idea or a source run ID');
      return;
    }

    setIsRunning(true);
    try {
      const payload: Record<string, unknown> = {};

      if (ideaInput.trim()) {
        // Parse idea input as JSON or create simple object
        try {
          payload.idea = JSON.parse(ideaInput);
        } catch {
          // Create simple idea object from text
          payload.idea = {
            title: ideaInput,
            description: 'User-provided idea',
            market_size: 'Unknown',
            complexity: 'Unknown',
          };
        }
      } else {
        payload.run_id = sourceRunId.trim();
      }

      const response = await submit('research.validate_idea', payload);

      setCurrentRun(response.run_id);
      // Start polling for completion
      pollValidation(response.run_id);
    } catch (error) {
      console.error('Validation failed:', error);
      alert('Validation failed. Please try again.');
    } finally {
      setIsRunning(false);
    }
  };

  const pollValidation = async (runId: string) => {
    try {
      const run = (await pollRun(runId, { timeoutMs: 60000, intervalMs: 1000 })) as {
        status: string;
        detail?: { error?: string };
      };

      if (run.status === 'succeeded') {
        setCurrentRun(null);
        fetchValidations(); // Refresh the list
      } else if (run.status === 'failed') {
        setCurrentRun(null);
        alert(`Validation failed: ${run.detail?.error || 'Unknown error'}`);
      }
    } catch {
      setCurrentRun(null);
      alert('Validation failed or timed out');
    }
  };

  const filteredValidations = validations.filter(validation => {
    if (filterTrend && validation.trend_score < parseInt(filterTrend)) return false;
    if (filterSentiment && validation.sentiment.avg < parseFloat(filterSentiment)) return false;
    if (filterCompetition && validation.competition.count > parseInt(filterCompetition))
      return false;
    if (
      filterAction &&
      !validation.recommended_action.toLowerCase().includes(filterAction.toLowerCase())
    )
      return false;
    return true;
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Research & Validation Department</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Validation Controls */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Run Validation</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Idea JSON (or paste idea text)
              </label>
              <textarea
                value={ideaInput}
                onChange={e => setIdeaInput(e.target.value)}
                placeholder='{"title": "My Idea", "description": "Description", "market_size": "Large"}'
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={4}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Or Source Run ID
              </label>
              <input
                type="text"
                value={sourceRunId}
                onChange={e => setSourceRunId(e.target.value)}
                placeholder="Enter run ID from ideation"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              onClick={runValidation}
              disabled={isRunning}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRunning ? 'Running...' : 'Run Validation'}
            </button>

            <button
              onClick={async () => {
                const curl = generateCurl('research.validate_idea', {
                  idea: { title: 'Sample Idea', description: 'Sample description' },
                });
                await copyToClipboard(curl);
                alert('cURL command copied to clipboard!');
              }}
              className="w-full bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
            >
              Copy cURL for Debug
            </button>

            {currentRun && <div className="text-sm text-gray-500">Current run: {currentRun}</div>}
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Filters</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Min Trend Score
              </label>
              <input
                type="number"
                value={filterTrend}
                onChange={e => setFilterTrend(e.target.value)}
                placeholder="0-100"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Min Sentiment</label>
              <input
                type="number"
                value={filterSentiment}
                onChange={e => setFilterSentiment(e.target.value)}
                placeholder="0.0-1.0"
                step="0.1"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Competition
              </label>
              <input
                type="number"
                value={filterCompetition}
                onChange={e => setFilterCompetition(e.target.value)}
                placeholder="Number of competitors"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Action Contains
              </label>
              <input
                type="text"
                value={filterAction}
                onChange={e => setFilterAction(e.target.value)}
                placeholder="e.g., prototype, launch"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Link
              href="/business"
              className="block w-full bg-gray-100 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-200 text-center"
            >
              Back to Business
            </Link>
            <Link
              href="/runs"
              className="block w-full bg-gray-100 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-200 text-center"
            >
              View All Runs
            </Link>
          </div>
        </div>
      </div>

      {/* Validation Results */}
      <div className="mt-8">
        <h2 className="text-2xl font-bold mb-6">Validation Results</h2>

        {filteredValidations.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No validation results found. Run a validation to see results.
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredValidations.map((validation, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-3">{validation.idea.title}</h3>
                <p className="text-gray-600 mb-4">{validation.idea.description}</p>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <span className="font-medium">Trend Score:</span>
                    <span
                      className={`ml-2 px-2 py-1 rounded text-sm ${
                        validation.trend_score >= 70
                          ? 'bg-green-100 text-green-800'
                          : validation.trend_score >= 50
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {validation.trend_score}/100
                    </span>
                  </div>

                  <div>
                    <span className="font-medium">Sentiment:</span>
                    <span className="ml-2 text-sm text-gray-600">
                      {(validation.sentiment.avg * 100).toFixed(1)}%
                    </span>
                  </div>

                  <div>
                    <span className="font-medium">Market Size:</span>
                    <span className="ml-2 text-sm text-gray-600">
                      ${(validation.market_size.tam / 1000000).toFixed(0)}M TAM
                    </span>
                  </div>

                  <div>
                    <span className="font-medium">Competition:</span>
                    <span className="ml-2 text-sm text-gray-600">
                      {validation.competition.count} competitors
                    </span>
                  </div>
                </div>

                <div className="mb-4">
                  <span className="font-medium">Recommended Action:</span>
                  <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                    {validation.recommended_action}
                  </span>
                </div>

                <div className="text-sm text-gray-500">
                  <div>Run ID: {validation.run_id}</div>
                  <div>Validated: {new Date(validation.validation_timestamp).toLocaleString()}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Runs Panel */}
      <div className="mt-8">
        <RecentRunsPanel defaultIntent="research.validate_idea" />
      </div>
    </div>
  );
}
