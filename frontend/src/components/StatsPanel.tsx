'use client';

import { useState, useEffect } from 'react';
import { supportAPI } from '@/lib/api';

interface Stats {
  total_queries: number;
  avg_confidence: number;
  automation_rate: number;
  automated_queries: number;
  human_required: number;
  categories: Record<string, number>;
}

export function StatsPanel() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [isOpen, setIsOpen] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await supportAPI.getStats();
        setStats(data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 10000); // Update every 10s

    return () => clearInterval(interval);
  }, []);

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed right-0 top-1/2 -translate-y-1/2 bg-white border border-l-0 border-gray-200 rounded-l-lg px-2 py-4 hover:bg-gray-50"
      >
        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </button>
    );
  }

  return (
    <aside className="w-80 bg-white border-l border-gray-200 flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <h2 className="font-semibold text-gray-900">Statystyki</h2>
        <button
          onClick={() => setIsOpen(false)}
          className="text-gray-400 hover:text-gray-600"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Stats Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {stats ? (
          <>
            {/* Key Metrics */}
            <div className="space-y-4">
              <StatCard
                label="Wszystkie zapytania"
                value={stats.total_queries}
                icon="📊"
              />
              <StatCard
                label="Automatyzacja"
                value={`${stats.automation_rate.toFixed(1)}%`}
                icon="🤖"
                color={stats.automation_rate >= 50 ? 'green' : 'orange'}
              />
              <StatCard
                label="Śr. pewność"
                value={`${(stats.avg_confidence * 100).toFixed(0)}%`}
                icon="🎯"
                color={stats.avg_confidence >= 0.8 ? 'green' : 'orange'}
              />
            </div>

            {/* Automation Breakdown */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Podział zapytań
              </h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Zautomatyzowane</span>
                  <span className="font-medium text-green-600">
                    {stats.automated_queries}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Wymagają człowieka</span>
                  <span className="font-medium text-orange-600">
                    {stats.human_required}
                  </span>
                </div>
              </div>
            </div>

            {/* Categories */}
            {Object.keys(stats.categories).length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">
                  Kategorie zapytań
                </h3>
                <div className="space-y-2">
                  {Object.entries(stats.categories)
                    .sort(([, a], [, b]) => b - a)
                    .map(([category, count]) => (
                      <div
                        key={category}
                        className="flex items-center justify-between text-sm"
                      >
                        <span className="text-gray-600 capitalize">
                          {category}
                        </span>
                        <span className="font-medium text-gray-900">
                          {count}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="flex items-center justify-center h-32 text-gray-400">
            Ładowanie statystyk...
          </div>
        )}
      </div>
    </aside>
  );
}

function StatCard({
  label,
  value,
  icon,
  color = 'blue'
}: {
  label: string;
  value: string | number;
  icon: string;
  color?: 'blue' | 'green' | 'orange';
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    orange: 'bg-orange-50 text-orange-700'
  };

  return (
    <div className={`rounded-lg p-4 ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium opacity-80">{label}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
        </div>
        <span className="text-3xl">{icon}</span>
      </div>
    </div>
  );
}
