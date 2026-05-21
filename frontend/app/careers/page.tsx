"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import api from "@/lib/api";

type Job = {
  id: string;
  title: string;
  location: string | null;
  employment_type: string | null;
  description: string;
  created_at: string;
};

export default function CareersPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const res = await api.get<{ items: Job[] }>("/api/jobs/public/list");
        setJobs(res.data.items || []);
      } catch (err) {
        setError("Failed to load positions.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchJobs();
  }, []);

  return (
    <div className="min-h-screen bg-[#fdf8f3] font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 h-14 flex items-center justify-between px-10 bg-[rgba(253,248,243,0.92)] backdrop-blur-2xl border-b border-[rgba(232,223,214,0.6)]">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[#3525cd]" />
          <span className="text-sm font-extrabold text-[#1d1b19] tracking-tight">AuraRecruiting</span>
        </div>
        <Link href="/" className="text-[0.85rem] font-medium text-[#515f74] hover:text-[#1d1b19] transition-colors">
          ← Back to Home
        </Link>
      </nav>

      {/* Main Content */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="mb-16">
            <h1 className="text-5xl font-extrabold tracking-[-0.035em] leading-tight text-[#1d1b19] mb-6">
              Build the future of talent.
            </h1>
            <p className="text-[#515f74] text-xl leading-relaxed max-w-2xl">
              Join a world-class team solving the hardest problems in recruitment through AI and human-centered design.
            </p>
          </div>
          
          <div className="space-y-12">
            <section id="openings">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-2xl font-bold text-[#1d1b19]">Open Positions ({jobs.length})</h2>
                <div className="h-0.5 flex-1 bg-[#f8f3ee] ml-6" />
              </div>

              {loading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-24 bg-white rounded-2xl animate-pulse border border-[#e8dfd6]" />
                  ))}
                </div>
              ) : error ? (
                <div className="p-8 bg-red-50 text-red-700 rounded-2xl border border-red-100">
                  {error}
                </div>
              ) : jobs.length === 0 ? (
                <div className="p-12 text-center bg-white rounded-3xl border border-[#e8dfd6]">
                  <p className="text-[#515f74] font-medium">No open roles at the moment. Check back soon!</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {jobs.map((job) => (
                    <Link
                      key={job.id}
                      href={`/careers/${job.id}`}
                      className="group block bg-white p-6 rounded-2xl border border-[#e8dfd6] hover:border-[#3525cd] hover:shadow-[0_8px_30px_rgba(53,37,205,0.06)] transition-all transform hover:-translate-y-1"
                    >
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <h3 className="text-xl font-bold text-[#1d1b19] group-hover:text-[#3525cd] transition-colors mb-2">
                            {job.title}
                          </h3>
                          <div className="flex items-center gap-4 text-sm text-[#515f74]">
                            <span className="flex items-center gap-1.5">
                              📍 {job.location || "Remote"}
                            </span>
                            <span className="w-1 h-1 rounded-full bg-[#e8dfd6]" />
                            <span className="flex items-center gap-1.5 capitalize">
                              💼 {job.employment_type?.replace("-", " ") || "Full-time"}
                            </span>
                          </div>
                        </div>
                        <div className="w-10 h-10 rounded-full bg-[#fdf8f3] group-hover:bg-[#3525cd] flex items-center justify-center text-[#3525cd] group-hover:text-white transition-all">
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <path d="M5 12h14M12 5l7 7-7 7" />
                          </svg>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </section>

            <section className="bg-white rounded-[2rem] p-10 border border-[#e8dfd6]">
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-6">Why AuraRecruiting?</h2>
              <div className="grid md:grid-cols-3 gap-8">
                <div>
                  <div className="w-10 h-10 rounded-lg bg-[rgba(53,37,205,0.08)] flex items-center justify-center text-[#3525cd] mb-4">
                    🚀
                  </div>
                  <h4 className="font-bold text-[#1d1b19] mb-2">High Impact</h4>
                  <p className="text-sm text-[#515f74] leading-relaxed">Work on the core engine that powers how thousands of companies find talent.</p>
                </div>
                <div>
                  <div className="w-10 h-10 rounded-lg bg-[rgba(16,185,129,0.08)] flex items-center justify-center text-green-600 mb-4">
                    🛠️
                  </div>
                  <h4 className="font-bold text-[#1d1b19] mb-2">Modern Tech</h4>
                  <p className="text-sm text-[#515f74] leading-relaxed">Built with Next.js, FastAPI, and state-of-the-art AI models like Gemini.</p>
                </div>
                <div>
                  <div className="w-10 h-10 rounded-lg bg-[rgba(245,158,11,0.08)] flex items-center justify-center text-amber-600 mb-4">
                    🌎
                  </div>
                  <h4 className="font-bold text-[#1d1b19] mb-2">Remote First</h4>
                  <p className="text-sm text-[#515f74] leading-relaxed">Join a distributed team across 4 continents. We value output over hours.</p>
                </div>
              </div>
            </section>

            <section className="text-center py-10">
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Don't see a fit?</h2>
              <p className="text-[#515f74] mb-8">We're always looking for brilliant people. Drop us a line.</p>
              <a href="mailto:careers@aurarecruiting.com" className="inline-flex items-center gap-2 text-[0.9rem] font-bold text-white px-8 py-3 rounded-full bg-[#1d1b19] hover:bg-[#2d2926] transition-all">
                General Application
              </a>
            </section>
          </div>
        </div>
      </section>
    </div>
  );
}
