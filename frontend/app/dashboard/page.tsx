"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/lib/protected-route";
import { useAuth } from "@/lib/auth-context";
import api from "@/lib/api";
import { normalizeRole } from "@/lib/permissions";
import { Skeleton, SkeletonCard } from "@/components/ui/skeleton";


type RecentJob = {
  id: string;
  title: string;
  status: string;
  location: string;
  matches_count: number;
};

type LatestActivity = {
  type: string;
  message: string;
  timestamp: string;
  link: string;
};

type DashboardData = {
  jobs_count: number;
  resumes_count: number;
  matches_count: number;
  recent_jobs: RecentJob[];
  latest_activity?: LatestActivity[];
};

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const role = normalizeRole(user?.role);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    const fetchData = async () => {
      try {
        const res = await api.get<DashboardData>("/api/analytics/dashboard");
        setData(res.data);
      } catch (error) {
        console.error("Failed to load dashboard data", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [user]);

  return (
    <ProtectedRoute>
      <div className="bg-[#fef8f3] min-h-screen p-8">
        <div className="max-w-6xl mx-auto space-y-6">

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-[#1d1b19]">
                Welcome back, {user?.full_name || user?.email} 👋
              </h1>
              <p className="text-sm text-[#515f74]">
                Here&apos;s what&apos;s happening with your talent pipeline today
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-[#3525cd] bg-[#3525cd]/10 px-3 py-1 rounded-full uppercase tracking-wide">
                {role}
              </span>
              <button
                onClick={logout}
                className="px-4 py-2 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg text-sm font-medium hover:bg-[#f8f3ee] transition-colors"
              >
                Sign out
              </button>
              <Link
                href="/jobs"
                className="px-5 py-2 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-lg text-sm font-semibold hover:shadow-lg transition-all"
              >
                + Post a Job
              </Link>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {loading ? (
              <>
                <SkeletonCard />
                <SkeletonCard />
                <SkeletonCard />
              </>
            ) : (
              <>
                <MetricCard
                  title="Total Jobs"
                  value={data?.jobs_count ?? 0}
                  delta="Active postings"
                  href="/jobs"
                />
                <MetricCard
                  title="Total Resumes"
                  value={data?.resumes_count ?? 0}
                  delta="Uploaded candidates"
                  href="/resumes"
                />
                <MetricCard
                  title="Total Matches"
                  value={data?.matches_count ?? 0}
                  delta="AI-generated matches"
                  href="/jobs"
                />
              </>
            )}
          </div>

          <div className="bg-white rounded-2xl p-6">
            <h2 className="text-base font-bold text-[#1d1b19] mb-4">Quick Actions</h2>
            <div className="grid grid-cols-4 gap-3">
              <Link
                href="/jobs"
                className="px-4 py-3 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-xl text-sm font-semibold text-center hover:shadow-lg transition-all"
              >
                + Create Job
              </Link>
              <Link
                href="/resumes"
                className="px-4 py-3 bg-[#f8f3ee] text-[#1d1b19] rounded-xl text-sm font-semibold text-center hover:bg-[#f3ede6] transition-colors"
              >
                ↑ Upload Resume
              </Link>
              <Link
                href="/analytics"
                className="px-4 py-3 bg-[#f8f3ee] text-[#1d1b19] rounded-xl text-sm font-semibold text-center hover:bg-[#f3ede6] transition-colors"
              >
                Analytics
              </Link>
              <Link
                href="/linkedin-generator"
                className="px-4 py-3 bg-[#f8f3ee] text-[#1d1b19] rounded-xl text-sm font-semibold text-center hover:bg-[#f3ede6] transition-colors"
              >
                LinkedIn Post
              </Link>
            </div>
          </div>

          <div className="grid grid-cols-5 gap-6">
            <div className="col-span-3 bg-white rounded-2xl overflow-hidden">
              <div className="flex items-center justify-between px-6 py-4 border-b border-[#f8f3ee]">
                <h2 className="text-base font-bold text-[#1d1b19]">Recent Jobs</h2>
                <Link
                  href="/jobs"
                  className="text-sm font-semibold text-[#3525cd] hover:underline"
                >
                  View all →
                </Link>
              </div>

              {loading ? (
                <div className="p-6 space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="flex items-center justify-between gap-4">
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-3 w-1/2" />
                      </div>
                      <Skeleton className="h-8 w-16 rounded-lg" />
                    </div>
                  ))}
                </div>
              ) : !data || data.recent_jobs.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 gap-3">
                  <div className="w-14 h-14 bg-[#f8f3ee] rounded-full flex items-center justify-center text-2xl">
                    📋
                  </div>
                  <p className="text-sm font-semibold text-[#1d1b19]">No jobs posted yet</p>
                  <Link
                    href="/jobs"
                    className="px-4 py-2 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-lg text-sm font-semibold hover:shadow-lg transition-all"
                  >
                    Create your first job
                  </Link>
                </div>
              ) : (
                <div className="divide-y divide-[#f8f3ee]">
                  {data.recent_jobs.map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center justify-between px-6 py-4 hover:bg-[#fef8f3] transition-colors gap-4"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-[#1d1b19] truncate mb-1">
                          {job.title}
                        </p>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span
                            className={
                              job.status === "active"
                                ? "text-xs font-semibold text-green-600 bg-green-100 px-2 py-0.5 rounded-full"
                                : "text-xs font-semibold text-[#8a5b00] bg-[#fff3d8] px-2 py-0.5 rounded-full"
                            }
                          >
                            {job.status}
                          </span>
                          <span className="text-xs text-[#515f74]">
                            {job.location || "Remote"}
                          </span>
                          <span className="text-xs font-medium text-[#3525cd]">
                            {job.matches_count} matches
                          </span>
                        </div>
                      </div>
                      <Link
                        href={`/jobs/${job.id}`}
                        className="px-3 py-1.5 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg text-xs font-medium hover:bg-[#f8f3ee] transition-colors flex-shrink-0"
                      >
                        View →
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="col-span-2 bg-white rounded-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-[#f8f3ee]">
                <h2 className="text-base font-bold text-[#1d1b19]">Latest Activity</h2>
              </div>

              {loading ? (
                <div className="p-6 space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="flex justify-between gap-4">
                      <Skeleton className="h-4 flex-1" />
                      <Skeleton className="h-3 w-12" />
                    </div>
                  ))}
                </div>
              ) : !data?.latest_activity || data.latest_activity.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 gap-2">
                  <p className="text-sm font-semibold text-[#1d1b19]">No activity yet</p>
                  <p className="text-xs text-[#515f74]">Actions will appear here</p>
                </div>
              ) : (
                <div className="divide-y divide-[#f8f3ee]">
                  {data.latest_activity.map((activity, idx) => (
                    <div
                      key={`${activity.timestamp}-${idx}`}
                      className="px-6 py-3 hover:bg-[#fef8f3] transition-colors flex items-start justify-between gap-3"
                    >
                      <Link
                        href={activity.link}
                        className="flex-1 text-sm text-[#1d1b19] hover:text-[#3525cd] transition-colors leading-snug"
                      >
                        {activity.message}
                      </Link>
                      <span className="flex-shrink-0 text-xs text-[#515f74] mt-0.5">
                        {formatRelativeTime(activity.timestamp)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </ProtectedRoute>
  );
}

function formatRelativeTime(timestamp: string): string {
  const eventTime = new Date(timestamp);
  if (Number.isNaN(eventTime.getTime())) return "just now";

  const now = new Date();
  const diffMs = now.getTime() - eventTime.getTime();
  const minuteMs = 60 * 1000;
  const hourMs = 60 * minuteMs;
  const dayMs = 24 * hourMs;

  if (diffMs < minuteMs) return "just now";
  if (diffMs < hourMs) return `${Math.floor(diffMs / minuteMs)}m ago`;
  if (diffMs < dayMs) return `${Math.floor(diffMs / hourMs)}h ago`;
  if (diffMs < dayMs * 7) return `${Math.floor(diffMs / dayMs)}d ago`;

  return eventTime.toLocaleDateString();
}

function MetricCard({
  title,
  value,
  delta,
  href,
}: {
  title: string;
  value: number;
  delta: string;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="bg-white rounded-2xl p-5 hover:shadow-md transition-shadow"
    >
      <p className="text-xs font-semibold text-[#515f74] mb-2">{title}</p>
      <p className="text-3xl font-bold text-[#1d1b19] mb-1">{value}</p>
      <p className="text-xs text-[#515f74]">{delta}</p>
    </Link>
  );
}