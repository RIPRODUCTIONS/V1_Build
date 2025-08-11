"use client";
import { useEffect, useState } from "react";

type Idea = {
  title: string;
  description: string;
  category: string;
  complexity: string;
  market_size: string;
  time_to_market: string;
  opportunity_score?: number;
  market_sentiment?: {
    score: number;
    confidence: number;
    sources: string[];
  };
  trend_data?: {
    trend_score: number;
    growth_rate: string;
  };
  competition?: {
    competition_level: string;
    market_maturity: string;
    differentiation_opportunity: string;
  };
};

type MarketAnalysis = {
  idea_id: number;
  title: string;
  market_analysis: {
    total_addressable_market: string;
    serviceable_market: string;
    market_growth_rate: string;
    customer_segments: string[];
    pricing_strategy: {
      model: string;
      pricing: string;
      tiers: string[];
    };
  };
  technical_analysis: {
    tech_stack: {
      backend: string[];
      frontend: string[];
      infrastructure: string[];
    };
    development_phases: Array<{
      phase: string;
      duration: string;
      deliverables: string[];
    }>;
    resource_requirements: {
      team_size: string;
      roles: string[];
      timeline: string;
      budget: string;
    };
  };
  business_model: {
    revenue_streams: string[];
    cost_structure: Record<string, string>;
    break_even_timeline: string;
  };
};

type Run = {
  run_id: string;
  status: string;
  detail?: any;
  result?: {
    ideas?: Idea[];
    validated_ideas?: Idea[];
    market_analysis?: MarketAnalysis[];
    next_steps?: string[];
  };
};

export default function BusinessDepartment() {
  const [runs, setRuns] = useState<Record<string, Run>>({});
  const [currentRun, setCurrentRun] = useState<string | null>(null);
  const [ideaTopic, setIdeaTopic] = useState("business automation");
  const [ideaCount, setIdeaCount] = useState(5);
  const [includeResearch, setIncludeResearch] = useState(true);

  async function poll(id: string) {
    try {
      const r = await fetch(`/api/automation/runs/${id}`).then((x) => x.json());
      setRuns((prev) => ({ ...prev, [id]: r }));

      // If run completed, set as current
      if (r.status === "succeeded" && !currentRun) {
        setCurrentRun(id);
      }
    } catch (error) {
      console.error("Failed to poll run:", error);
    }
  }

  useEffect(() => {
    const t = setInterval(() => {
      Object.keys(runs).forEach((id) => poll(id));
    }, 1000);
    return () => clearInterval(t);
  }, [runs]);

  const runIdeaEngine = async (pipeline: "generate" | "full") => {
    const intent = pipeline === "full" ? "ideation.full_pipeline" : "ideation.generate";

    try {
      const response = await fetch("/api/automation/submit", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          intent,
          payload: {
            topic: ideaTopic,
            count: ideaCount,
            include_research: includeResearch,
          },
          idempotency_key: crypto.randomUUID(),
        }),
      });

      const result = await response.json();
      setRuns((prev) => ({ ...prev, [result.run_id]: { run_id: result.run_id, status: "queued" } }));
      setCurrentRun(result.run_id);
    } catch (error) {
      console.error("Failed to run idea engine:", error);
    }
  };

  const runFullResearchPipeline = async () => {
    try {
      // First, run the idea engine
      const ideaResponse = await fetch("/api/automation/submit", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          intent: "ideation.generate",
          payload: {
            topic: ideaTopic,
            count: ideaCount,
            include_research: false, // We'll do research separately
          },
          idempotency_key: crypto.randomUUID(),
        }),
      });

      const ideaResult = await ideaResponse.json();
      const ideaRunId = ideaResult.run_id;

      // Add idea run to tracking
      setRuns((prev) => ({ ...prev, [ideaRunId]: { run_id: ideaRunId, status: "queued" } }));

      // Wait for idea generation to complete, then trigger research validation
      const pollIdeaCompletion = async () => {
        try {
          const ideaRun = await fetch(`/api/automation/runs/${ideaRunId}`).then((x) => x.json());

          if (ideaRun.status === "succeeded" && ideaRun.result?.ideas) {
            // Idea generation completed, now run research validation
            const researchResponse = await fetch("/api/research/validate", {
              method: "POST",
              headers: { "content-type": "application/json" },
              body: JSON.stringify({
                run_id: ideaRunId,
              }),
            });

            if (researchResponse.ok) {
              const researchResult = await researchResponse.json();
              const researchRunId = researchResult.run_id;

              // Add research run to tracking
              setRuns((prev) => ({ ...prev, [researchRunId]: { run_id: researchRunId, status: "queued" } }));
              setCurrentRun(researchRunId);

              console.log("Full pipeline started: Idea → Research", {
                ideaRunId,
                researchRunId,
                correlationId: researchResult.correlation_id,
              });
            }
          } else if (ideaRun.status === "failed") {
            console.error("Idea generation failed:", ideaRun);
          } else {
            // Still running, poll again in 2 seconds
            setTimeout(pollIdeaCompletion, 2000);
          }
        } catch (error) {
          console.error("Failed to poll idea completion:", error);
        }
      };

      // Start polling for idea completion
      setTimeout(pollIdeaCompletion, 2000);

    } catch (error) {
      console.error("Failed to start full research pipeline:", error);
    }
  };

  const getCurrentResults = () => {
    if (!currentRun || !runs[currentRun]) return null;
    return runs[currentRun].result;
  };

  const formatScore = (score: number) => {
    return `${(score * 100).toFixed(1)}%`;
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.7) return "text-green-600";
    if (score >= 0.5) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Business Department</h1>
          <p className="mt-2 text-gray-600">
            AI-powered business intelligence and opportunity identification
          </p>
        </div>

        {/* Idea Engine Controls */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Idea Engine</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Business Topic
              </label>
              <input
                type="text"
                value={ideaTopic}
                onChange={(e) => setIdeaTopic(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., business automation"
              />
            </div>

            <div>
              <label htmlFor="ideaCount" className="block text-sm font-medium text-gray-700 mb-2">
                Number of Ideas
              </label>
              <select
                id="ideaCount"
                value={ideaCount}
                onChange={(e) => setIdeaCount(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={3}>3 ideas</option>
                <option value={5}>5 ideas</option>
                <option value={10}>10 ideas</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="includeResearch"
                checked={includeResearch}
                onChange={(e) => setIncludeResearch(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="includeResearch" className="ml-2 text-sm text-gray-700">
                Include market research
              </label>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => runIdeaEngine("generate")}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Generate Ideas
            </button>

            <button
              onClick={() => runIdeaEngine("full")}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
            >
              Full Pipeline (Generate + Research + Analysis)
            </button>

            <button
              onClick={() => runFullResearchPipeline()}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
            >
              Run Full Pipeline (Idea → Research)
            </button>
          </div>
        </div>

        {/* Active Runs */}
        {Object.keys(runs).length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Runs</h3>
            <div className="space-y-3">
              {Object.entries(runs).map(([id, run]) => (
                <div key={id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                  <div className="flex items-center space-x-3">
                    <div className="text-sm font-mono text-gray-600">{id}</div>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                      run.status === "succeeded" ? "bg-green-100 text-green-800" :
                      run.status === "failed" ? "bg-red-100 text-red-800" :
                      run.status === "running" ? "bg-blue-100 text-blue-800" :
                      "bg-gray-100 text-gray-800"
                    }`}>
                      {run.status}
                    </div>
                  </div>

                  {run.detail?.executed && (
                    <div className="text-sm text-gray-600">
                      {run.detail.executed.join(" → ")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Results Display */}
        {currentRun && runs[currentRun]?.status === "succeeded" && (
          <div className="space-y-8">
            {/* Generated Ideas */}
            {getCurrentResults()?.ideas && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  Generated Ideas ({getCurrentResults()?.ideas?.length || 0})
                </h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {getCurrentResults()?.ideas?.map((idea: Idea, index: number) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-semibold text-gray-900 mb-2">{idea.title}</h4>
                      <p className="text-gray-600 text-sm mb-3">{idea.description}</p>

                      <div className="grid grid-cols-2 gap-2 text-xs text-gray-500 mb-3">
                        <div>Category: {idea.category}</div>
                        <div>Complexity: {idea.complexity}</div>
                        <div>Market: {idea.market_size}</div>
                        <div>Timeline: {idea.time_to_market}</div>
                      </div>

                      {idea.opportunity_score && (
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-700">Opportunity Score:</span>
                          <span className={`font-bold ${getScoreColor(idea.opportunity_score)}`}>
                            {formatScore(idea.opportunity_score)}
                          </span>
                        </div>
                      )}

                      {idea.market_sentiment && (
                        <div className="mt-3 pt-3 border-t border-gray-100">
                          <div className="flex items-center justify-between text-xs">
                            <span>Market Sentiment:</span>
                            <span className={getScoreColor(idea.market_sentiment.score)}>
                              {formatScore(idea.market_sentiment.score)}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Market Analysis */}
            {getCurrentResults()?.market_analysis && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  Market Analysis
                </h3>
                <div className="space-y-6">
                  {getCurrentResults()?.market_analysis?.map((analysis: MarketAnalysis) => (
                    <div key={analysis.idea_id} className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-semibold text-gray-900 mb-3">{analysis.title}</h4>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Market Analysis */}
                        <div>
                          <h5 className="font-medium text-gray-900 mb-2">Market Analysis</h5>
                          <div className="space-y-2 text-sm">
                            <div><span className="font-medium">TAM:</span> {analysis.market_analysis.total_addressable_market}</div>
                            <div><span className="font-medium">SAM:</span> {analysis.market_analysis.serviceable_market}</div>
                            <div><span className="font-medium">Growth:</span> {analysis.market_analysis.market_growth_rate}</div>
                            <div><span className="font-medium">Pricing:</span> {analysis.market_analysis.pricing_strategy.pricing}</div>
                          </div>
                        </div>

                        {/* Technical Analysis */}
                        <div>
                          <h5 className="font-medium text-gray-900 mb-2">Technical Analysis</h5>
                          <div className="space-y-2 text-sm">
                            <div><span className="font-medium">Team:</span> {analysis.technical_analysis.resource_requirements.team_size}</div>
                            <div><span className="font-medium">Timeline:</span> {analysis.technical_analysis.resource_requirements.timeline}</div>
                            <div><span className="font-medium">Budget:</span> {analysis.technical_analysis.resource_requirements.budget}</div>
                          </div>
                        </div>

                        {/* Business Model */}
                        <div>
                          <h5 className="font-medium text-gray-900 mb-2">Business Model</h5>
                          <div className="space-y-2 text-sm">
                            <div><span className="font-medium">Break-even:</span> {analysis.business_model.break_even_timeline}</div>
                            <div><span className="font-medium">Revenue Streams:</span> {analysis.business_model.revenue_streams.length}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Next Steps */}
            {getCurrentResults()?.next_steps && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Recommended Next Steps</h3>
                <div className="space-y-2">
                  {getCurrentResults()?.next_steps?.map((step: string, index: number) => (
                    <div key={index} className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                        {index + 1}
                      </div>
                      <p className="text-gray-700">{step}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* No Results State */}
        {currentRun && runs[currentRun]?.status === "succeeded" && !getCurrentResults() && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-center">
            <p className="text-gray-500">No results available for this run.</p>
          </div>
        )}
      </div>
    </div>
  );
}
