"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ProtectedRoute } from "@/lib/protected-route";
import api from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { toast } from "sonner";
import { canManageJobs, canReviewMatches } from "@/lib/permissions";

type Job = {
  id: string;
  title: string;
  description: string;
  requirements: string | null;
  responsibilities: string | null;
  required_skills: string[];
  preferred_skills: string[] | null;
  location: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  status: "draft" | "active" | "paused" | "closed";
  employment_type: "full-time" | "part-time" | "contract" | "internship" | null;
  experience_required: number | null;
  education_required: string | null;
  created_at: string;
};

type JobUpdatePayload = Partial<{
  title: string;
  description: string;
  requirements: string;
  responsibilities: string;
  required_skills: string[];
  preferred_skills: string[];
  location: string;
  salary_min: number | null;
  salary_max: number | null;
  experience_required: number | null;
  education_required: string;
  employment_type: "full-time" | "part-time" | "contract" | "internship";
  status: "draft" | "active" | "paused" | "closed";
}>;

type MatchItem = {
  id: string;
  job_description_id: string;
  resume_id: string;
  overall_score: number;
  skill_match_score?: number | null;
  experience_match_score?: number | null;
  education_match_score?: number | null;
  recruiter_status: string;
  recruiter_notes: string | null;
  matched_skills: string[] | null;
  missing_skills: string[] | null;
  match_reasoning: string | null;
  created_at: string;
};

type MatchListResponse = {
  items: MatchItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

type MatchDraft = {
  recruiter_status: string;
  recruiter_notes: string;
};

type ResumeItem = {
  id: string;
  candidate_name: string;
  file_name: string;
  skills: string[];
  experience_years: number | null;
};

type ResumeListResponse = {
  items: ResumeItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

function daysAgo(timestamp: string): string {
  const t = new Date(timestamp).getTime();
  if (Number.isNaN(t)) return "recently";
  const diffDays = Math.max(0, Math.floor((Date.now() - t) / (1000 * 60 * 60 * 24)));
  if (diffDays === 0) return "today";
  if (diffDays === 1) return "1 day ago";
  return `${diffDays} days ago`;
}

function normalizeScore(value: number | null | undefined, fallback: number): number {
  const v = typeof value === "number" ? value : fallback;
  return Math.max(0, Math.min(100, v));
}

function ScoreBar({ label, value, note }: { label: string; value: number; note?: string }) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between">
        <span className="text-sm font-medium text-[#1d1b19]">{label}</span>
        <span className="text-sm text-[#515f74]">
          {value.toFixed(0)}% {note ? note : ""}
        </span>
      </div>
      <div className="w-full h-2 bg-[#e8dfd6] rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-[#3525cd] to-[#4f46e5] transition-all"
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

export default function JobDetailPage() {
  const { user } = useAuth();
  const canManageJob = canManageJobs(user?.role);
  const canReview = canReviewMatches(user?.role);
  const params = useParams<{ id: string }>();
  const jobId = params?.id;
  const [job, setJob] = useState<Job | null>(null);
  const [jobForm, setJobForm] = useState<JobUpdatePayload>({});
  const [matches, setMatches] = useState<MatchItem[]>([]);
  const [matchDrafts, setMatchDrafts] = useState<Record<string, MatchDraft>>({});
  const [matchPage, setMatchPage] = useState(1);
  const [matchPageSize] = useState(10);
  const [matchTotalPages, setMatchTotalPages] = useState(1);
  const [matchTotal, setMatchTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [savingJob, setSavingJob] = useState(false);
  const [updatingMatchId, setUpdatingMatchId] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [validationError, setValidationError] = useState("");
  const [activeTab, setActiveTab] = useState<"all" | "new" | "shortlisted" | "rejected">("all");
  const [sortBy, setSortBy] = useState<"best" | "newest" | "oldest">("best");
  const [bulkAction, setBulkAction] = useState<"" | "shortlisted" | "rejected" | "reviewed">("");
  const [selectedMatchIds, setSelectedMatchIds] = useState<string[]>([]);
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [resumeLoading, setResumeLoading] = useState(false);
  const [selectedResumeIds, setSelectedResumeIds] = useState<string[]>([]);
  const [analyzingSelected, setAnalyzingSelected] = useState(false);
  const [analyzingUpload, setAnalyzingUpload] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [viewMode, setViewMode] = useState<"list" | "kanban">("list");

  const loadPage = useCallback(async () => {
    if (!jobId) return;
    setLoading(true);
    setError("");
    try {
      const [jobRes, matchRes] = await Promise.all([
        api.get<Job>(`/api/jobs/${jobId}`),
        api.get<MatchListResponse>("/api/matches/job", {
          params: { job_id: jobId, page: matchPage, page_size: matchPageSize },
        }),
      ]);
      setJob(jobRes.data);
      setJobForm({
        title: jobRes.data.title,
        description: jobRes.data.description,
        requirements: jobRes.data.requirements || "",
        responsibilities: jobRes.data.responsibilities || "",
        required_skills: jobRes.data.required_skills || [],
        preferred_skills: jobRes.data.preferred_skills || [],
        location: jobRes.data.location || "",
        salary_min: jobRes.data.salary_min ?? undefined,
        salary_max: jobRes.data.salary_max ?? undefined,
        experience_required: jobRes.data.experience_required || undefined,
        education_required: jobRes.data.education_required || "",
        employment_type: jobRes.data.employment_type || undefined,
        status: jobRes.data.status,
      });
      setMatches(matchRes.data.items);
      setMatchTotalPages(matchRes.data.total_pages || 1);
      setMatchTotal(matchRes.data.total);
      const drafts: Record<string, MatchDraft> = {};
      matchRes.data.items.forEach((item) => {
        drafts[item.id] = {
          recruiter_status: item.recruiter_status,
          recruiter_notes: item.recruiter_notes || "",
        };
      });
      setMatchDrafts(drafts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load job details");
    } finally {
      setLoading(false);
    }
  }, [jobId, matchPage, matchPageSize]);

  useEffect(() => {
    loadPage();
  }, [loadPage]);

  const loadResumes = useCallback(async () => {
    setResumeLoading(true);
    try {
      const res = await api.get<ResumeListResponse>("/api/resumes", {
        params: { page: 1, page_size: 100 },
      });
      setResumes(res.data.items || []);
    } catch (err) {
      console.warn("Resumes not available:", err);
      setResumes([]);
    } finally {
      setResumeLoading(false);
    }
  }, []);

  useEffect(() => {
    loadResumes();
  }, [loadResumes]);

  const countsByStatus = useMemo(() => {
    const counts = { all: matches.length, new: 0, shortlisted: 0, rejected: 0 };
    matches.forEach((m) => {
      const status = (m.recruiter_status || "").toLowerCase();
      if (status === "new") counts.new += 1;
      if (status === "shortlisted") counts.shortlisted += 1;
      if (status === "rejected") counts.rejected += 1;
    });
    return counts;
  }, [matches]);

  const visibleMatches = useMemo(() => {
    let rows = [...matches];
    if (activeTab !== "all") {
      rows = rows.filter((m) => (m.recruiter_status || "").toLowerCase() === activeTab);
    }
    if (sortBy === "best") {
      rows.sort((a, b) => b.overall_score - a.overall_score);
    } else if (sortBy === "newest") {
      rows.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    } else {
      rows.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    }
    return rows;
  }, [matches, activeTab, sortBy]);

  const onGenerateMatches = async () => {
    if (!canManageJob) {
      toast.error("Only admins can generate matches.");
      return;
    }
    if (!jobId) return;
    setGenerating(true);
    setError("");
    try {
      await api.post<MatchListResponse, undefined>(`/api/matches/generate?job_id=${jobId}&limit=50`, undefined);
      setMatchPage(1);
      toast.success("Matches generated");
      await loadPage();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate matches");
      toast.error(err instanceof Error ? err.message : "Failed to generate matches");
    } finally {
      setGenerating(false);
    }
  };

  const onSaveJob = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!canManageJob) {
      toast.error("Only admins can update jobs.");
      return;
    }
    if ((jobForm.title || "").trim().length < 5) {
      const msg = "Title must be at least 5 characters.";
      setValidationError(msg);
      toast.error(msg);
      return;
    }
    if ((jobForm.description || "").trim().length < 50) {
      const msg = "Description must be at least 50 characters.";
      setValidationError(msg);
      toast.error(msg);
      return;
    }
    setValidationError("");
    if (!jobId) return;
    setSavingJob(true);
    setError("");
    try {
      await api.patch<Job, JobUpdatePayload>(`/api/jobs/${jobId}`, jobForm);
      toast.success("Job updated");
      await loadPage();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update job");
      toast.error(err instanceof Error ? err.message : "Failed to update job");
    } finally {
      setSavingJob(false);
    }
  };

  const onSaveMatch = async (matchId: string, override?: MatchDraft) => {
    if (!canReview) {
      toast.error("Your role cannot update match review.");
      return;
    }
    const draft = override || matchDrafts[matchId];
    if (!draft) return;
    const previousMatches = matches;
    const previousMatch = matches.find((match) => match.id === matchId);
    setMatches((current) =>
      current.map((match) =>
        match.id === matchId
          ? {
              ...match,
              recruiter_status: draft.recruiter_status,
              recruiter_notes: draft.recruiter_notes,
            }
          : match
      )
    );
    setUpdatingMatchId(matchId);
    setError("");
    try {
      await api.patch<MatchItem, { recruiter_status: string; recruiter_notes: string }>(
        `/api/matches/${matchId}`,
        {
          recruiter_status: draft.recruiter_status,
          recruiter_notes: draft.recruiter_notes,
        }
      );
      toast.success("Match updated");
    } catch (err) {
      setMatches(previousMatches);
      if (previousMatch) {
        setMatchDrafts((current) => ({
          ...current,
          [matchId]: {
            recruiter_status: previousMatch.recruiter_status,
            recruiter_notes: previousMatch.recruiter_notes || "",
          },
        }));
      }
      setError(err instanceof Error ? err.message : "Failed to update match");
      toast.error(err instanceof Error ? err.message : "Failed to update match");
    } finally {
      setUpdatingMatchId(null);
    }
  };

  const toggleResumeSelection = (resumeId: string) => {
    setSelectedResumeIds((current) =>
      current.includes(resumeId) ? current.filter((id) => id !== resumeId) : [...current, resumeId]
    );
  };

  const onSyncPortal = async () => {
    try {
      setResumeLoading(true);
      const res = await api.post<{ message: string; count: number }>("/api/resumes/sync", {});
      toast.success(res.data.message);
      await loadResumes();
    } catch (err) {
      console.error("Sync failed", err);
      toast.error("Failed to sync from portal");
    } finally {
      setResumeLoading(false);
    }
  };

  const onAnalyzeSelectedResumes = async () => {
    if (!canManageJob) {
      toast.error("Only admins can analyze resumes.");
      return;
    }
    if (!jobId) return;
    if (selectedResumeIds.length === 0) {
      toast.error("Select at least one saved resume.");
      return;
    }
    setAnalyzingSelected(true);
    try {
      await api.post("/api/matches/generate-selected", {
        job_id: jobId,
        resume_ids: selectedResumeIds,
        limit: Math.min(100, selectedResumeIds.length),
      });
      toast.success("Selected resumes analyzed");
      setSelectedResumeIds([]);
      await loadPage();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to analyze selected resumes";
      const userFriendlyMsg = errorMsg.includes("image input")
        ? "Unable to analyze resume. Please ensure files are in PDF or DOC format."
        : errorMsg;
      setError(userFriendlyMsg);
      toast.error(userFriendlyMsg);
    } finally {
      setAnalyzingSelected(false);
    }
  };

  const onUploadAndAnalyzeResume = async () => {
    if (!canManageJob) {
      toast.error("Only admins can analyze resumes.");
      return;
    }
    if (!jobId) return;
    if (!uploadFile) {
      toast.error("Choose a resume file to upload.");
      return;
    }

    setAnalyzingUpload(true);
    try {
      const form = new FormData();
      form.append("file", uploadFile);
      const uploadRes = await api.postForm<{ id: string }>("/api/resumes/upload", form);
      const resumeId = uploadRes.data.id;

      await api.post("/api/matches/generate-selected", {
        job_id: jobId,
        resume_ids: [resumeId],
        limit: 1,
      });

      setUploadFile(null);
      toast.success("Resume uploaded, parsed, and analyzed for this job");
      await Promise.all([loadPage(), loadResumes()]);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to upload and analyze resume";
      const userFriendlyMsg = errorMsg.includes("image input")
        ? "Unable to process file. Please upload PDF or DOC format."
        : errorMsg;
      setError(userFriendlyMsg);
      toast.error(userFriendlyMsg);
    } finally {
      setAnalyzingUpload(false);
    }
  };

  const toggleSelection = (matchId: string) => {
    setSelectedMatchIds((current) =>
      current.includes(matchId) ? current.filter((id) => id !== matchId) : [...current, matchId]
    );
  };

  const applyBulkAction = async () => {
    if (!canReview) {
      toast.error("Your role cannot update match review.");
      return;
    }
    if (!bulkAction) {
      toast.error("Select a bulk action first.");
      return;
    }
    if (selectedMatchIds.length === 0) {
      toast.error("Select at least one match.");
      return;
    }

    for (const id of selectedMatchIds) {
      const notes = matchDrafts[id]?.recruiter_notes || "";
      const nextDraft: MatchDraft = {
        recruiter_status: bulkAction,
        recruiter_notes: notes,
      };
      setMatchDrafts((current) => ({
        ...current,
        [id]: nextDraft,
      }));
      await onSaveMatch(id, nextDraft);
    }

    setSelectedMatchIds([]);
    toast.success("Bulk action applied");
  };

  const exportMatchesCsv = () => {
    const headers = ["rank", "resume_id", "overall_score", "status", "matched_skills", "missing_skills", "reasoning"];
    const rows = visibleMatches.map((m, idx) => [
      String(idx + 1),
      m.resume_id,
      m.overall_score.toFixed(2),
      m.recruiter_status,
      (m.matched_skills || []).join("|"),
      (m.missing_skills || []).join("|"),
      (m.match_reasoning || "").replace(/\n/g, " "),
    ]);
    const csv = [headers, ...rows]
      .map((row) =>
        row
          .map((cell) => `"${String(cell).replace(/"/g, '""')}"`)
          .join(",")
      )
      .join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `matches-${job?.title || "job"}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-[#fef8f3]">


        {/* Main Content */}
        <main className="flex-1 overflow-auto flex flex-col">
          {/* Top Bar */}
          <div className="sticky top-0 z-10 bg-white border-b border-[#e8dfd6] px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Link
    href="/jobs"
    className="flex items-center gap-2 px-5 py-2 bg-[#3525cd] text-white text-sm font-semibold rounded-lg hover:bg-[#4f46e5] hover:shadow-md transition-all"
  >
    ← Back to Jobs
  </Link>
                 
              </div>
              <button
                onClick={onGenerateMatches}
                disabled={generating || !canManageJob}
                className="px-6 py-2 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-lg font-medium hover:shadow-lg transition-all disabled:opacity-50"
              >
                {generating ? "Generating..." : "Generate Matches"}
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-auto p-8">
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 mb-4">
                {error}
              </div>
            )}
            {validationError && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700 mb-4">
                {validationError}
              </div>
            )}

            {loading ? (
              <div className="space-y-4 max-w-4xl">
                <div className="h-12 bg-[#e8dfd6] rounded animate-pulse" />
                <div className="h-32 bg-[#e8dfd6] rounded animate-pulse" />
                <div className="h-20 bg-[#e8dfd6] rounded animate-pulse" />
              </div>
            ) : !job ? (
              <div className="p-8 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700 text-center max-w-4xl">
                <p>Job not found</p>
                <Link href="/jobs" className="text-yellow-600 hover:underline text-sm font-medium mt-4 inline-block">
                  Back to Jobs
                </Link>
              </div>
            ) : (
              <div className="max-w-4xl space-y-8">
                {/* Job Header */}
                <div className="bg-white rounded-2xl p-8">
                  <h1 className="text-4xl font-bold text-[#1d1b19] mb-2">{job.title}</h1>
                  <div className="flex items-center gap-3 flex-wrap">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        job.status === "active"
                          ? "bg-[#3525cd]/10 text-[#3525cd]"
                          : job.status === "draft"
                          ? "bg-[#515f74]/10 text-[#515f74]"
                          : "bg-orange-100 text-orange-700"
                      }`}
                    >
                      {job.status}
                    </span>
                     <span className="text-[#515f74] text-sm">📍 {job.location || "Remote"}</span>
<span className="text-[#515f74] text-sm">💼 {job.employment_type || "Full-time"}</span>
{job.experience_required && (
  <span className="text-[#515f74] text-sm">📅 {job.experience_required}+ years</span>
)}
                  </div>
                  {(job.salary_min || job.salary_max) && (
                    <div className="mt-4 p-4 bg-[#f8f3ee] rounded-lg">
                      <p className="text-sm text-[#515f74]">Salary Range</p>
                      <p className="text-xl font-bold text-[#3525cd]">
                        {job.salary_min ? `â‚¹${job.salary_min.toLocaleString()}` : ""}{" "}
                        {job.salary_min && job.salary_max ? "â€”" : ""}{" "}
                        {job.salary_max ? `â‚¹${job.salary_max.toLocaleString()}` : ""}
                      </p>
                    </div>
                  )}
                </div>

                {/* Job Edit Form */}
                <div className="bg-white rounded-2xl p-8">
                  <h2 className="text-2xl font-bold text-[#1d1b19] mb-6">Job Details</h2>
                  {!canManageJob && (
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-700 text-sm mb-4">
                      Read-only mode: only admins can edit jobs.
                    </div>
                  )}
                  <form onSubmit={onSaveJob} className="space-y-6">
                    <div>
                      <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Job Title</label>
                      <input
                        type="text"
                        className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                        value={jobForm.title || ""}
                        onChange={(e) => setJobForm((f) => ({ ...f, title: e.target.value }))}
                        required
                        minLength={5}
                        disabled={!canManageJob}
                      />
                    </div>

                    <div>
                      <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Description</label>
                      <textarea
                        className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors resize-none disabled:opacity-50"
                        rows={4}
                        value={jobForm.description || ""}
                        onChange={(e) => setJobForm((f) => ({ ...f, description: e.target.value }))}
                        required
                        minLength={50}
                        disabled={!canManageJob}
                      />
                    </div>

                    <div>
                      <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Requirements</label>
                      <textarea
                        className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors resize-none disabled:opacity-50"
                        rows={4}
                        value={jobForm.requirements || ""}
                        onChange={(e) => setJobForm((f) => ({ ...f, requirements: e.target.value }))}
                        disabled={!canManageJob}
                      />
                    </div>

                    <div>
                      <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Responsibilities</label>
                      <textarea
                        className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors resize-none disabled:opacity-50"
                        rows={4}
                        value={jobForm.responsibilities || ""}
                        onChange={(e) => setJobForm((f) => ({ ...f, responsibilities: e.target.value }))}
                        disabled={!canManageJob}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Required Skills</label>
                        <input
                          type="text"
                          className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                          placeholder="Python, FastAPI, PostgreSQL"
                          value={(jobForm.required_skills || []).join(", ")}
                          onChange={(e) =>
                            setJobForm((f) => ({
                              ...f,
                              required_skills: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                            }))
                          }
                          disabled={!canManageJob}
                        />
                      </div>
                      <div>
                        <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Preferred Skills</label>
                        <input
                          type="text"
                          className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                          placeholder="React, Redis, Kubernetes"
                          value={(jobForm.preferred_skills || []).join(", ")}
                          onChange={(e) =>
                            setJobForm((f) => ({
                              ...f,
                              preferred_skills: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                            }))
                          }
                          disabled={!canManageJob}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Location</label>
                        <input
                          type="text"
                          className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                          placeholder="Remote"
                          value={jobForm.location || ""}
                          onChange={(e) => setJobForm((f) => ({ ...f, location: e.target.value }))}
                          disabled={!canManageJob}
                        />
                      </div>
                      <div>
                        <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Experience (years)</label>
                        <input
                          type="number"
                          min={0}
                          max={50}
                          className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                          value={jobForm.experience_required ?? ""}
                          onChange={(e) =>
                            setJobForm((f) => ({
                              ...f,
                              experience_required: e.target.value ? Number(e.target.value) : null,
                            }))
                          }
                          disabled={!canManageJob}
                        />
                      </div>
                      <div>
                        <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Status</label>
                        <select
                          className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                          value={jobForm.status || "draft"}
                          onChange={(e) =>
                            setJobForm((f) => ({
                              ...f,
                              status: e.target.value as Job["status"],
                            }))
                          }
                          disabled={!canManageJob}
                        >
                          <option value="draft">Draft</option>
                          <option value="active">Active</option>
                          <option value="paused">Paused</option>
                          <option value="closed">Closed</option>
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Salary Min</label>
                        <input
                          type="number"
                          min={0}
                          className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                          value={jobForm.salary_min ?? ""}
                          onChange={(e) =>
                            setJobForm((f) => ({
                              ...f,
                              salary_min: e.target.value ? Number(e.target.value) : null,
                            }))
                          }
                          disabled={!canManageJob}
                        />
                      </div>
                      <div>
                        <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Salary Max</label>
                        <input
                          type="number"
                          min={0}
                          className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                          value={jobForm.salary_max ?? ""}
                          onChange={(e) =>
                            setJobForm((f) => ({
                              ...f,
                              salary_max: e.target.value ? Number(e.target.value) : null,
                            }))
                          }
                          disabled={!canManageJob}
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={savingJob || !canManageJob}
                      className="px-6 py-3 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-lg font-medium hover:shadow-lg transition-all disabled:opacity-50"
                    >
                      {savingJob ? "Saving..." : "Save Job"}
                    </button>
                  </form>
                </div>

                                 {/* Analyze Resumes */}
                <div className="bg-white rounded-2xl p-8">
                  <h2 className="text-2xl font-bold text-[#1d1b19] mb-6">Analyze Resumes For This Job</h2>
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-semibold text-[#1d1b19] mb-4">Upload & Analyze Resume</h3>
                      <input
                        type="file"
                        accept=".pdf,.doc,.docx"
                        onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                        className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] focus:outline-none focus:ring-2 focus:ring-[#3525cd] mb-3 disabled:opacity-50"
                        disabled={!canManageJob || analyzingUpload}
                      />
                      <button
                        type="button"
                        onClick={onUploadAndAnalyzeResume}
                        disabled={!canManageJob || analyzingUpload || !uploadFile}
                        className="w-full px-6 py-3 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg font-medium hover:bg-[#f8f3ee] transition-colors disabled:opacity-50"
                      >
                        {analyzingUpload ? "Analyzing..." : "Upload + Analyze"}
                      </button>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-[#1d1b19]">Analyze Saved Resumes</h3>
                        <button
                          type="button"
                          onClick={onSyncPortal}
                          disabled={resumeLoading || !canManageJob}
                          className="text-xs font-semibold text-[#3525cd] hover:underline flex items-center gap-1"
                        >
                          {resumeLoading ? "Syncing..." : "🔄 Sync Portal"}
                        </button>
                      </div>
                        {resumes.length > 0 && (
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={resumes.length > 0 && selectedResumeIds.length === resumes.length}
                              onChange={(e) =>
                                e.target.checked ? setSelectedResumeIds(resumes.map((r) => r.id)) : setSelectedResumeIds([])
                              }
                              disabled={!canManageJob || analyzingSelected}
                              className="rounded"
                            />
                            <span className="text-sm font-medium text-[#515f74]">Select All</span>
                          </label>
                        )}
                      {resumeLoading ? (
                        <p className="text-[#515f74] text-sm">Loading resumes...</p>
                      ) : resumes.length === 0 ? (
                        <p className="text-[#515f74] text-sm">No saved resumes found.</p>
                      ) : (
                        <>
                          <div className="space-y-2 mb-3 max-h-40 overflow-y-auto border border-[#e8dfd6] rounded-lg p-2">
                            {resumes.map((resume) => (
                              <label key={resume.id} className="flex items-center gap-2 p-2 hover:bg-[#f8f3ee] rounded cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={selectedResumeIds.includes(resume.id)}
                                  onChange={() => toggleResumeSelection(resume.id)}
                                  disabled={!canManageJob || analyzingSelected}
                                  className="rounded"
                                />
                                <span className="text-sm text-[#1d1b19]">{resume.candidate_name}</span>
                              </label>
                            ))}
                          </div>
                          <button
                            type="button"
                            onClick={onAnalyzeSelectedResumes}
                            disabled={!canManageJob || analyzingSelected || selectedResumeIds.length === 0}
                            className="w-full px-6 py-3 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg font-medium hover:bg-[#f8f3ee] transition-colors disabled:opacity-50"
                          >
                            {analyzingSelected ? "Analyzing..." : `Analyze Selected (${selectedResumeIds.length})`}
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Matches Section */}
                <div className="bg-white rounded-2xl p-8">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-[#1d1b19]">Matches ({matchTotal})</h2>
                    <div className="flex items-center gap-2">
                      <div className="flex p-1 bg-[#f8f3ee] rounded-xl mr-4">
                        <button
                          onClick={() => setViewMode("list")}
                          className={`px-4 py-1.5 rounded-lg text-sm font-bold transition-all ${
                            viewMode === "list" ? "bg-white text-[#3525cd] shadow-sm" : "text-[#515f74] hover:text-[#1d1b19]"
                          }`}
                        >
                          List
                        </button>
                        <button
                          onClick={() => setViewMode("kanban")}
                          className={`px-4 py-1.5 rounded-lg text-sm font-bold transition-all ${
                            viewMode === "kanban" ? "bg-white text-[#3525cd] shadow-sm" : "text-[#515f74] hover:text-[#1d1b19]"
                          }`}
                        >
                          Kanban
                        </button>
                      </div>
                      <button
                        onClick={exportMatchesCsv}
                        className="px-4 py-2 text-sm bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg font-medium hover:bg-[#f8f3ee] transition-colors"
                      >
                        Export CSV
                      </button>
                    </div>
                  </div>

                  {viewMode === "kanban" ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 min-h-[500px]">
                      {(["new", "shortlisted", "rejected"] as const).map((colStatus) => {
                        const colMatches = matches.filter(
                          (m) => (m.recruiter_status || "").toLowerCase() === colStatus
                        );
                        return (
                          <div key={colStatus} className="bg-[#f8f3ee]/50 rounded-2xl p-4 border border-[#e8dfd6]/50 flex flex-col">
                            <div className="flex items-center justify-between mb-4 px-2">
                              <h3 className="text-sm font-bold text-[#1d1b19] uppercase tracking-wider">
                                {colStatus} ({colMatches.length})
                              </h3>
                              <div className={`w-2 h-2 rounded-full ${
                                colStatus === "new" ? "bg-[#3525cd]" 
                                : colStatus === "shortlisted" ? "bg-green-500" 
                                : "bg-red-500"
                              }`} />
                            </div>
                            
                            <div className="space-y-4 flex-1">
                              {colMatches.length === 0 ? (
                                <div className="border border-dashed border-[#e8dfd6] rounded-xl p-8 text-center">
                                  <p className="text-xs text-[#515f74]">No candidates</p>
                                </div>
                              ) : (
                                colMatches.map((m) => {
                                  const resumeData = resumes.find(r => r.id === m.resume_id);
                                  const candidateName = resumeData?.candidate_name || m.resume_id.slice(0, 8);
                                  const overall = normalizeScore(m.overall_score, 0);
                                  
                                  return (
                                    <div key={m.id} className="bg-white p-4 rounded-xl border border-[#e8dfd6] shadow-sm hover:shadow-md transition-all group">
                                      <div className="flex justify-between items-start mb-2">
                                        <p className="font-bold text-[#1d1b19] text-sm truncate">{candidateName}</p>
                                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                          overall >= 75 ? "bg-green-50 text-green-700" : "bg-blue-50 text-blue-700"
                                        }`}>
                                          {overall.toFixed(0)}%
                                        </span>
                                      </div>
                                      
                                      <div className="flex flex-wrap gap-1 mb-3">
                                        {(m.matched_skills || []).slice(0, 3).map(s => (
                                          <span key={s} className="px-1.5 py-0.5 bg-[#f8f3ee] text-[#515f74] text-[9px] rounded">
                                            {s}
                                          </span>
                                        ))}
                                      </div>

                                      <div className="flex items-center justify-between pt-3 border-t border-[#f8f3ee] gap-1">
                                        {colStatus !== "shortlisted" && (
                                          <button 
                                            onClick={() => onSaveMatch(m.id, { ...matchDrafts[m.id], recruiter_status: "shortlisted" })}
                                            className="flex-1 py-1.5 text-[10px] font-bold bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors"
                                          >
                                            Shortlist
                                          </button>
                                        )}
                                        {colStatus === "new" && (
                                           <button 
                                            onClick={() => onSaveMatch(m.id, { ...matchDrafts[m.id], recruiter_status: "rejected" })}
                                            className="flex-1 py-1.5 text-[10px] font-bold bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors"
                                          >
                                            Reject
                                          </button>
                                        )}
                                        {colStatus !== "new" && (
                                          <button 
                                            onClick={() => onSaveMatch(m.id, { ...matchDrafts[m.id], recruiter_status: "new" })}
                                            className="px-2 py-1.5 text-[10px] font-bold bg-[#f8f3ee] text-[#515f74] rounded-lg hover:bg-[#e8dfd6] transition-colors"
                                          >
                                            Reset
                                          </button>
                                        )}
                                      </div>
                                    </div>
                                  );
                                })
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <>
                  {/* Tabs & Filters */}
                  <div className="mb-6 space-y-4">
                    <div className="flex gap-4 border-b border-[#e8dfd6]">
                      {(["all", "new", "shortlisted", "rejected"] as const).map((tab) => (
                        <button
                          key={tab}
                          onClick={() => setActiveTab(tab)}
                          className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                            activeTab === tab
                              ? "border-[#3525cd] text-[#3525cd]"
                              : "border-transparent text-[#515f74] hover:text-[#1d1b19]"
                          }`}
                        >
                          {tab.charAt(0).toUpperCase() + tab.slice(1)} ({countsByStatus[tab]})
                        </button>
                      ))}
                    </div>

                    <div className="flex gap-2">
                      <select
                        value={bulkAction}
                        onChange={(e) => setBulkAction(e.target.value as "" | "shortlisted" | "rejected" | "reviewed")}
                        className="px-4 py-2 bg-[#f8f3ee] rounded-lg text-sm text-[#1d1b19] focus:outline-none focus:ring-2 focus:ring-[#3525cd]"
                      >
                        <option value="">Bulk Actions</option>
                        <option value="shortlisted">Mark Shortlisted</option>
                        <option value="rejected">Mark Rejected</option>
                        <option value="reviewed">Mark Reviewed</option>
                      </select>
                      <button
                        onClick={applyBulkAction}
                        disabled={!bulkAction || selectedMatchIds.length === 0 || !canReview}
                        className="px-4 py-2 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg text-sm font-medium hover:bg-[#f8f3ee] transition-colors disabled:opacity-50"
                      >
                        Apply ({selectedMatchIds.length})
                      </button>
                      <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value as "best" | "newest" | "oldest")}
                        className="px-4 py-2 bg-[#f8f3ee] rounded-lg text-sm text-[#1d1b19] focus:outline-none focus:ring-2 focus:ring-[#3525cd]"
                      >
                        <option value="best">Best Match</option>
                        <option value="newest">Newest</option>
                        <option value="oldest">Oldest</option>
                      </select>
                    </div>
                  </div>

                  {visibleMatches.length === 0 ? (
                    <div className="text-center py-12">
                      <p className="text-[#515f74]">No matches found. Generate matches to get started.</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {visibleMatches.map((m, idx) => {
                        const overall = normalizeScore(m.overall_score, 0);
                        const skill = normalizeScore(m.skill_match_score, overall);
                        const exp = normalizeScore(m.experience_match_score, overall);
                        const edu = normalizeScore(m.education_match_score, overall);
                        const draft = matchDrafts[m.id] || { recruiter_status: m.recruiter_status, recruiter_notes: "" };
                        const resumeData = resumes.find(r => r.id === m.resume_id);
                        const candidateName = resumeData?.candidate_name || m.resume_id.slice(0, 8);
                        return (
                          <div key={m.id} className="border border-[#e8dfd6] rounded-xl p-6 space-y-4">
                            <div className="flex items-start justify-between">
                              <div className="flex items-center gap-3">
                                <input
                                  type="checkbox"
                                  checked={selectedMatchIds.includes(m.id)}
                                  onChange={() => toggleSelection(m.id)}
                                  className="rounded"
                                />
                                <div>
                                  <p className="font-semibold text-[#1d1b19]">#{idx + 1} · {candidateName}</p>
                                  <p className="text-xs text-[#515f74]">Matched {daysAgo(m.created_at)}</p>
                                </div>
                              </div>
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                overall >= 75 ? "bg-green-100 text-green-700"
                                  : overall >= 50 ? "bg-yellow-100 text-yellow-700"
                                  : "bg-red-100 text-red-700"
                              }`}>
                                {overall.toFixed(0)}%
                              </span>
                            </div>

                            <div className="space-y-2">
                              <ScoreBar label="Overall" value={overall} />
                              <ScoreBar label="Skills" value={skill} />
                              <ScoreBar label="Experience" value={exp} />
                              <ScoreBar label="Education" value={edu} />
                            </div>

                            {(m.matched_skills?.length || m.missing_skills?.length) ? (
                              <div className="grid grid-cols-2 gap-4">
                                {m.matched_skills?.length ? (
                                  <div>
                                    <p className="text-xs font-semibold text-green-700 mb-1">✓ Matched</p>
                                    <div className="flex flex-wrap gap-1">
                                      {m.matched_skills.map((s) => (
                                        <span key={s} className="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded-full">{s}</span>
                                      ))}
                                    </div>
                                  </div>
                                ) : null}
                                {m.missing_skills?.length ? (
                                  <div>
                                    <p className="text-xs font-semibold text-red-600 mb-1">✗ Missing</p>
                                    <div className="flex flex-wrap gap-1">
                                      {m.missing_skills.length > 4 ? (
                                        <>
                                          {m.missing_skills.slice(0, 2).map((s) => (
                                            <span key={s} className="px-2 py-0.5 bg-red-50 text-red-600 text-xs rounded-full">{s}</span>
                                          ))}
                                          <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full font-bold">
                                            + {m.missing_skills.length - 2} more
                                          </span>
                                        </>
                                      ) : (
                                        m.missing_skills.map((s) => (
                                          <span key={s} className="px-2 py-0.5 bg-red-50 text-red-600 text-xs rounded-full">{s}</span>
                                        ))
                                      )}
                                    </div>
                                  </div>
                                ) : null}
                              </div>
                            ) : null}

                            {m.match_reasoning && (
                              <p className="text-sm text-[#515f74] bg-[#f8f3ee] rounded-lg p-3">{m.match_reasoning}</p>
                            )}

                             <div>
  <label className="text-xs font-semibold text-[#1d1b19] block mb-2">Status</label>
  <div className="flex flex-wrap gap-2">
    {(["new", "reviewed", "shortlisted", "rejected"] as const).map((status) => (
      <button
        key={status}
        type="button"
        disabled={!canReview}
        onClick={async () => {
  const newDraft = { ...draft, recruiter_status: status };
  setMatchDrafts((cur) => ({
    ...cur,
    [m.id]: newDraft,
  }));
  await onSaveMatch(m.id, newDraft);
}} 
        className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all disabled:opacity-50 ${
          draft.recruiter_status === status
            ? status === "shortlisted"
              ? "bg-green-500 text-white border-green-500"
              : status === "rejected"
              ? "bg-red-500 text-white border-red-500"
              : status === "reviewed"
              ? "bg-blue-500 text-white border-blue-500"
              : "bg-[#3525cd] text-white border-[#3525cd]"
            : "bg-white text-[#515f74] border-[#e8dfd6] hover:border-[#3525cd] hover:text-[#3525cd]"
        }`}
      >
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </button>
    ))}
  </div>
</div>
                              <div>
                                <label className="text-xs font-semibold text-[#1d1b19] block mb-1">Notes</label>
                                <input
                                  type="text"
                                  value={draft.recruiter_notes}
                                  onChange={(e) =>
                                    setMatchDrafts((cur) => ({
                                      ...cur,
                                      [m.id]: { ...draft, recruiter_notes: e.target.value },
                                    }))
                                  }
                                  disabled={!canReview}
                                  placeholder="Add notes..."
                                  className="w-full bg-[#f8f3ee] px-3 py-2 rounded-lg text-sm text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] disabled:opacity-50"
                                />
                              </div>
                            

                            <div className="flex justify-end">
                              <button
                                onClick={() => onSaveMatch(m.id)}
                                disabled={!canReview || updatingMatchId === m.id}
                                className="px-4 py-2 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white text-sm rounded-lg font-medium hover:shadow-lg transition-all disabled:opacity-50"
                              >
                                {updatingMatchId === m.id ? "Saving..." : "Save"}
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {viewMode === "list" && matchTotalPages > 1 && (
                    <div className="mt-6 flex items-center justify-between pt-6 border-t border-[#e8dfd6]">
                      <p className="text-sm text-[#515f74]">
                        Page {matchPage} of {matchTotalPages}
                      </p>
                      <div className="flex gap-2">
                        <button
                          onClick={() => setMatchPage((p) => Math.max(1, p - 1))}
                          disabled={matchPage <= 1}
                          className="px-4 py-2 text-sm bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg font-medium hover:bg-[#f8f3ee] transition-colors disabled:opacity-50"
                        >
                          Previous
                        </button>
                        <button
                          onClick={() => setMatchPage((p) => Math.min(matchTotalPages, p + 1))}
                          disabled={matchPage >= matchTotalPages}
                          className="px-4 py-2 text-sm bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg font-medium hover:bg-[#f8f3ee] transition-colors disabled:opacity-50"
                        >
                          Next
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
