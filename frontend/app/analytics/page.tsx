"use client";

import { useEffect, useMemo, useState } from "react";
import { ProtectedRoute } from "@/lib/protected-route";
import api from "@/lib/api";

type OverviewData = {
  active_jobs: number;
  total_candidates: number;
  matches_generated: number;
  response_rate: number;
  jobs_delta: number;
  candidates_delta: number;
};

type FunnelData = {
  matches: number;
  reviewed: number;
  shortlisted: number;
  interviewed: number;
  offered: number;
};

type TopJob = {
  job_id: string;
  title: string;
  matches: number;
  shortlisted: number;
  days_open: number;
};

type QualityPoint = {
  label: string;
  avg_score: number;
};

type TimeToHire = {
  average_days: number;
  fastest_days: number;
  slowest_days: number;
};

type AnalyticsResponse = {
  days: number;
  overview: OverviewData;
  funnel: FunnelData;
  top_jobs: TopJob[];
  quality_trend: QualityPoint[];
  time_to_hire: TimeToHire;
};

export default function AnalyticsPage() {
  const [days, setDays] = useState<30 | 60 | 90>(30);
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const res = await api.get<AnalyticsResponse>("/api/analytics/overview", {
          params: { days },
        });
        if (active) setData(res.data);
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load analytics");
        }
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [days]);

  const funnelRows = useMemo(() => {
    if (!data) return [];
    const total = Math.max(1, data.funnel.matches);
    return [
      { label: "Matches", count: data.funnel.matches },
      { label: "Reviewed", count: data.funnel.reviewed },
      { label: "Shortlisted", count: data.funnel.shortlisted },
      { label: "Interviewed", count: data.funnel.interviewed },
      { label: "Offered", count: data.funnel.offered },
    ].map((row) => ({
      ...row,
      pct: Math.round((row.count / total) * 100),
    }));
  }, [data]);

  const exportCsv = () => {
    if (!data) return;

    const lines: (string | number)[][] = [
      ["section", "metric", "value"],
      ["overview", "active_jobs", data.overview.active_jobs],
      ["overview", "total_candidates", data.overview.total_candidates],
      ["overview", "matches_generated", data.overview.matches_generated],
      ["overview", "response_rate", data.overview.response_rate],
      ["time_to_hire", "average_days", data.time_to_hire.average_days],
      ["time_to_hire", "fastest_days", data.time_to_hire.fastest_days],
      ["time_to_hire", "slowest_days", data.time_to_hire.slowest_days],
    ];

    data.top_jobs.forEach((job) => {
      lines.push([
        "top_job",
        job.title,
        `${job.matches} matches, ${job.shortlisted} shortlisted, ${job.days_open} days`,
      ]);
    });

    data.quality_trend.forEach((p) => {
      lines.push(["quality_trend", p.label, p.avg_score]);
    });

    const sanitizeCsvCell = (value: string | number) => {
      const s = String(value);
      return /^[=+\-@]/.test(s) ? `'${s}` : s;
    };

    const csv = lines
      .map((row) =>
        row
          .map((c) => `"${sanitizeCsvCell(c).replace(/"/g, '""')}"`)
          .join(",")
      )
      .join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `analytics-last-${days}-days.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const funnelColors = [
    "bg-[#3525cd]",
    "bg-[#4f46e5]",
    "bg-[#818cf8]",
    "bg-[#a5b4fc]",
    "bg-[#c7d2fe]",
  ];

  return (
    <ProtectedRoute>
      <div className="bg-[#fef8f3] min-h-screen p-8">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-[#1d1b19]">Analytics</h1>
              <p className="text-sm text-[#515f74]">
                Track performance, match quality, and time-to-hire across every role
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex bg-white rounded-lg border border-[#e8dfd6] overflow-hidden">
                {([30, 60, 90] as const).map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setDays(d)}
                    className={
                      days === d
                        ? "px-4 py-2 text-sm font-semibold bg-[#3525cd] text-white transition-colors"
                        : "px-4 py-2 text-sm font-medium text-[#515f74] hover:bg-[#f8f3ee] transition-colors"
                    }
                  >
                    {d}d
                  </button>
                ))}
              </div>

              <button
                type="button"
                onClick={exportCsv}
                disabled={!data}
                className="px-4 py-2 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg text-sm font-medium hover:bg-[#f8f3ee] transition-colors disabled:opacity-50"
              >
                Export CSV
              </button>
            </div>
          </div>

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {loading || !data ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-white rounded-2xl p-6 animate-pulse">
                  <div className="h-4 bg-[#f8f3ee] rounded w-1/4 mb-4" />
                  <div className="grid grid-cols-4 gap-4">
                    {[1, 2, 3, 4].map((j) => (
                      <div key={j} className="h-20 bg-[#f8f3ee] rounded-xl" />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-4 gap-4">
                <MetricCard
                  
                  title="Active Jobs"
                  value={String(data.overview.active_jobs)}
                  delta={`${data.overview.jobs_delta >= 0 ? "+" : ""}${data.overview.jobs_delta} this period`}
                  positive={data.overview.jobs_delta >= 0}
                />
                <MetricCard
                  
                  title="Total Candidates"
                  value={String(data.overview.total_candidates)}
                  delta={`${data.overview.candidates_delta >= 0 ? "+" : ""}${data.overview.candidates_delta} this period`}
                  positive={data.overview.candidates_delta >= 0}
                />
                <MetricCard
                  
                  title="Matches Generated"
                  value={String(data.overview.matches_generated)}
                  delta="Total matches"
                  positive={true}
                />
                <MetricCard
                  
                  title="Response Rate"
                  value={`${data.overview.response_rate}%`}
                  delta="Candidate response"
                  positive={data.overview.response_rate >= 50}
                />
              </div>

              <div className="grid grid-cols-3 gap-6">
                <div className="col-span-2 bg-white rounded-2xl p-6">
                  <h2 className="text-base font-bold text-[#1d1b19] mb-1">Hiring Funnel</h2>
                  <p className="text-sm text-[#515f74] mb-5">Candidate progression through stages</p>

                  <div className="space-y-4">
                    {funnelRows.map((row, i) => (
                      <div key={row.label}>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-sm font-medium text-[#1d1b19]">{row.label}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-sm font-bold text-[#1d1b19]">{row.count}</span>
                            <span className="text-xs text-[#515f74] w-10 text-right">{row.pct}%</span>
                          </div>
                        </div>
                        <div className="h-2 bg-[#f8f3ee] rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${funnelColors[i]}`}
                            style={{ width: `${row.pct}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white rounded-2xl p-6">
                  <h2 className="text-base font-bold text-[#1d1b19] mb-1">Time to Hire</h2>
                  <p className="text-sm text-[#515f74] mb-5">Days from post to offer</p>

                  <div className="space-y-4">
                    <div className="bg-[#f8f3ee] rounded-xl p-4 text-center">
                      <p className="text-xs font-medium text-[#515f74] mb-1">Average</p>
                      <p className="text-3xl font-bold text-[#1d1b19]">{data.time_to_hire.average_days}</p>
                      <p className="text-xs text-[#515f74] mt-1">days</p>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-[#f8f3ee] rounded-xl p-3 text-center">
                        <p className="text-xs font-medium text-green-600 mb-1">Fastest</p>
                        <p className="text-2xl font-bold text-[#1d1b19]">{data.time_to_hire.fastest_days}</p>
                        <p className="text-xs text-[#515f74]">days</p>
                      </div>

                      <div className="bg-[#f8f3ee] rounded-xl p-3 text-center">
                        <p className="text-xs font-medium text-[#7e3000] mb-1">Slowest</p>
                        <p className="text-2xl font-bold text-[#1d1b19]">{data.time_to_hire.slowest_days}</p>
                        <p className="text-xs text-[#515f74]">days</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl p-6">
                <h2 className="text-base font-bold text-[#1d1b19] mb-1">Match Quality Trends</h2>
                <p className="text-sm text-[#515f74] mb-6">Average match score over time</p>

                <div className="flex items-end gap-3 h-40">
                  {data.quality_trend.map((p) => {
                    const h = Math.max(10, Math.min(100, p.avg_score));
                    return (
                      <div key={p.label} className="flex-1 flex flex-col items-center gap-2">
                        <span className="text-xs font-semibold text-[#3525cd]">
                          {p.avg_score.toFixed(0)}%
                        </span>
                        <div
                          className="w-full bg-[#f8f3ee] rounded-lg overflow-hidden flex items-end"
                          style={{ height: "100px" }}
                        >
                          <div
                            className="w-full bg-gradient-to-t from-[#3525cd] to-[#4f46e5] rounded-lg transition-all"
                            style={{ height: `${h}%` }}
                          />
                        </div>
                        <span className="text-xs text-[#515f74] text-center">{p.label}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="bg-white rounded-2xl p-6">
                <h2 className="text-base font-bold text-[#1d1b19] mb-1">Top Performing Jobs</h2>
                <p className="text-sm text-[#515f74] mb-5">Jobs with the most matches and activity</p>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-[#e8dfd6]">
                        <th className="text-left text-xs font-semibold text-[#515f74] pb-3 pr-4">
                          Job Title
                        </th>
                        <th className="text-right text-xs font-semibold text-[#515f74] pb-3 pr-4">
                          Matches
                        </th>
                        <th className="text-right text-xs font-semibold text-[#515f74] pb-3 pr-4">
                          Shortlisted
                        </th>
                        <th className="text-right text-xs font-semibold text-[#515f74] pb-3">
                          Days Open
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f8f3ee]">
                      {data.top_jobs.map((job) => (
                        <tr key={job.job_id} className="hover:bg-[#fef8f3] transition-colors">
                          <td className="py-3 pr-4 text-sm font-medium text-[#1d1b19]">
                            {job.title}
                          </td>
                          <td className="py-3 pr-4 text-sm text-[#515f74] text-right">
                            {job.matches}
                          </td>
                          <td className="py-3 pr-4 text-right">
                            <span className="text-xs font-semibold px-2 py-1 bg-[#3525cd]/10 text-[#3525cd] rounded-full">
                              {job.shortlisted}
                            </span>
                          </td>
                          <td className="py-3 text-sm text-[#515f74] text-right">
                            {job.days_open}d
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
function MetricCard({
  title,
  value,
  delta,
  positive,
}: {
  title: string;
  value: string;
  delta: string;
  positive: boolean;
}) {
  return (
    <div className="bg-white rounded-xl p-4">
      <p className="text-xs font-semibold text-[#515f74] mb-2">{title}</p>
      <p className="text-xl font-bold text-[#1d1b19] mb-1">{value}</p>
      <p
        className={
          positive
            ? "text-xs text-green-600 font-medium"
            : "text-xs text-red-500 font-medium"
        }
      >
        {delta}
      </p>
    </div>
  );
}
 