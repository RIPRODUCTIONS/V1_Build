'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';

import { useToast } from '@/components/ToastProvider';
import { apiFetch } from '@/lib/api';

type Department = {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  task_count: number;
};

type Task = {
  id: string;
  name: string;
  description: string;
  department: string;
  complexity: 'low' | 'medium' | 'high';
  estimated_duration: string;
  dependencies: string[];
};

type AutomationRun = {
  run_id: string;
  status: 'pending' | 'started' | 'completed' | 'failed';
  intent: string;
  department: string;
  correlation_id: string;
  created_at: string;
  meta?: unknown;
};

export default function Dashboard() {
  const { show } = useToast();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [taskCatalog, setTaskCatalog] = useState<Task[]>([]);
  const [recentRuns, setRecentRuns] = useState<AutomationRun[]>([]);
  const [managerStatus, setManagerStatus] = useState<'healthy' | 'degraded' | 'down'>('down');
  const [loading, setLoading] = useState(true);

  // Load AI departments and task catalog
  useEffect(() => {
    async function loadData() {
      try {
        const [deptRes, tasksRes, runsRes] = await Promise.all([
          apiFetch<Department[]>('/departments'),
          apiFetch<{ tasks: Task[] }>('/departments/tasks/catalog'),
          apiFetch<{ items: AutomationRun[] }>('/runs?limit=10'),
        ]);

        setDepartments(deptRes || []);
        setTaskCatalog(tasksRes?.tasks || []);
        setRecentRuns(runsRes?.items || []);

        // Check manager health
        try {
          const healthRes = await fetch('http://localhost:8080/health');
          setManagerStatus(healthRes.ok ? 'healthy' : 'degraded');
        } catch {
          setManagerStatus('down');
        }
      } catch {
        show('Failed to load AI Business Engine data', 'error');
      } finally {
        setLoading(false);
      }
    }

    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, [show]);

  const triggerLifeAutomation = async (endpoint: string, label: string) => {
    try {
      const res = await apiFetch<{ run_id: string; status: string }>(endpoint, {
        method: 'POST',
        body: JSON.stringify({}),
      });
      show(`${label} queued: ${res.run_id}`, 'success');
    } catch {
      show(`${label} failed`, 'error');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading AI Business Engine...</div>
      </div>
    );
  }

  return (
    <section className="space-y-8 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900">AI Business Engine</h1>
        <p className="text-xl text-gray-600">
          Autonomous AI agents running your business end-to-end
        </p>
        <div className="flex items-center justify-center gap-4">
          <div
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              managerStatus === 'healthy'
                ? 'bg-green-100 text-green-800'
                : managerStatus === 'degraded'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-red-100 text-red-800'
            }`}
          >
            Manager: {managerStatus}
          </div>
          <Link href="/runs" className="text-blue-600 hover:underline">
            Runs Console
          </Link>
          <Link href="/research" className="text-purple-600 hover:underline">
            Research & Validation
          </Link>
        </div>
      </div>

      {/* AI Departments */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">AI Departments</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {departments.map(dept => (
            <div
              key={dept.id}
              className="p-6 border rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow"
            >
              <h3 className="text-lg font-semibold mb-2">{dept.name}</h3>
              <p className="text-gray-600 mb-3">{dept.description}</p>
              <div className="mb-3">
                <span className="text-sm font-medium text-gray-700">Capabilities:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {dept.capabilities.slice(0, 3).map(cap => (
                    <span key={cap} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      {cap}
                    </span>
                  ))}
                  {dept.capabilities.length > 3 && (
                    <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                      +{dept.capabilities.length - 3} more
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">{dept.task_count} tasks available</span>
                <Link
                  href={`/departments/${dept.id}`}
                  className="text-blue-600 hover:underline text-sm"
                >
                  View Tasks
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Task Catalog Preview */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Available Tasks</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {taskCatalog.slice(0, 6).map(task => (
            <div key={task.id} className="p-4 border rounded-lg bg-white">
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-medium">{task.name}</h3>
                <span
                  className={`px-2 py-1 text-xs rounded ${
                    task.complexity === 'high'
                      ? 'bg-red-100 text-red-800'
                      : task.complexity === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-green-100 text-green-800'
                  }`}
                >
                  {task.complexity}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{task.description}</p>
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>{task.department}</span>
                <span>{task.estimated_duration}</span>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 text-center">
          <Link href="/departments/tasks" className="text-blue-600 hover:underline">
            View Full Task Catalog →
          </Link>
        </div>
      </div>

      {/* Life Automation */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Life Automation</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {[
            { path: '/life/health/wellness', label: 'Wellness', icon: '🏃‍♂️' },
            { path: '/life/nutrition/plan', label: 'Nutrition', icon: '🥗' },
            { path: '/life/home/evening', label: 'Home', icon: '🏠' },
            { path: '/life/transport/commute', label: 'Commute', icon: '🚗' },
            { path: '/life/learning/upskill', label: 'Learning', icon: '📚' },
            { path: '/life/finance/investments', label: 'Investments', icon: '📈' },
            { path: '/life/finance/bills', label: 'Bills', icon: '💰' },
            { path: '/life/security/sweep', label: 'Security', icon: '🔒' },
            { path: '/life/travel/plan', label: 'Travel', icon: '✈️' },
            { path: '/life/calendar/organize', label: 'Calendar', icon: '📅' },
            { path: '/life/shopping/optimize', label: 'Shopping', icon: '🛒' },
          ].map(automation => (
            <button
              key={automation.path}
              className="p-4 border rounded-lg bg-white hover:bg-gray-50 transition-colors text-center"
              onClick={() => triggerLifeAutomation(automation.path, automation.label)}
            >
              <div className="text-2xl mb-2">{automation.icon}</div>
              <div className="text-sm font-medium">{automation.label}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Research Department */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Research Department</h2>
        <div className="bg-white border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Market Gap Scanner</h3>
              <p className="text-gray-600 text-sm">AI-powered market opportunity identification</p>
            </div>
            <Link
              href="/research/market-gaps"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Open Scanner
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Capability:</span>
              <span className="ml-2 text-gray-600">Market Analysis</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Output:</span>
              <span className="ml-2 text-gray-600">Business Opportunities</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Frequency:</span>
              <span className="ml-2 text-gray-600">On-Demand</span>
            </div>
          </div>
        </div>
      </div>

      {/* Business Department */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Business Department</h2>
        <div className="bg-white border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Idea Engine</h3>
              <p className="text-gray-600 text-sm">
                AI-powered business idea generation and market validation
              </p>
            </div>
            <Link
              href="/business"
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Launch Idea Engine
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Capability:</span>
              <span className="ml-2 text-gray-600">Idea Generation & Validation</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Output:</span>
              <span className="ml-2 text-gray-600">Market-Validated Business Ideas</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Frequency:</span>
              <span className="ml-2 text-gray-600">On-Demand</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Automation Runs */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Recent Automation Runs</h2>
        <div className="bg-white border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Run ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Intent
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Department
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Correlation ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {recentRuns.map(run => (
                  <tr key={run.run_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-mono text-gray-900">
                      {run.run_id.slice(0, 8)}...
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          run.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : run.status === 'started'
                              ? 'bg-blue-100 text-blue-800'
                              : run.status === 'failed'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {run.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">{run.intent || 'N/A'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{run.department || 'N/A'}</td>
                    <td className="px-4 py-3 text-sm font-mono text-gray-500">
                      {run.correlation_id?.slice(0, 8) || 'N/A'}...
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {new Date(run.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {recentRuns.length === 0 && (
            <div className="p-8 text-center text-gray-500">
              No automation runs yet. Trigger some automations to see them here!
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            className="p-4 border rounded-lg bg-blue-50 hover:bg-blue-100 transition-colors text-center"
            onClick={() =>
              triggerLifeAutomation('/life/calendar/organize', 'Calendar Organization')
            }
          >
            <div className="text-2xl mb-2">📅</div>
            <div className="font-medium">Organize Calendar</div>
            <div className="text-sm text-gray-600">AI-powered scheduling</div>
          </button>

          <button
            className="p-4 border rounded-lg bg-green-50 hover:bg-green-100 transition-colors text-center"
            onClick={() =>
              triggerLifeAutomation('/life/finance/investments', 'Investment Analysis')
            }
          >
            <div className="text-2xl mb-2">📊</div>
            <div className="font-medium">Analyze Investments</div>
            <div className="text-sm text-gray-600">Portfolio optimization</div>
          </button>

          <button
            className="p-4 border rounded-lg bg-purple-50 hover:bg-purple-100 transition-colors text-center"
            onClick={() => triggerLifeAutomation('/life/learning/upskill', 'Learning Plan')}
          >
            <div className="text-2xl mb-2">🎯</div>
            <div className="font-medium">Create Learning Plan</div>
            <div className="text-sm text-gray-600">Skill development roadmap</div>
          </button>
        </div>
      </div>
    </section>
  );
}
