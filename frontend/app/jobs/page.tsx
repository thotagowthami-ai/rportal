"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/lib/protected-route";
import api from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { toast } from "sonner";
import { SkeletonRow } from "@/components/ui/skeleton";
import { Modal } from "@/components/ui/Modal";

import { canManageJobs } from "@/lib/permissions";

type Job = {
  id: string;
  title: string;
  description: string;
  requirements: string | null;
  responsibilities: string | null;
  required_skills: string[];
  preferred_skills: string[] | null;
  location: string | null;
  status: string;
  employment_type: string | null;
  experience_required: number | null;
  education_required: string | null;
  created_at: string;
  updated_at: string;
};

type JobListResponse = {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

type CreateMode = "structured" | "plain_text";

type CreateJobPayload = {
  title: string;
  description: string;
  requirements: string;
  responsibilities: string;
  required_skills: string[];
  preferred_skills: string[];
  location: string;
  education_required: string;
  experience_required: number | null;
  salary_min: number | null;
  salary_max: number | null;
  employment_type: "full-time" | "part-time" | "contract" | "internship";
  status: "draft" | "active" | "paused" | "closed";
};

const emptyForm: CreateJobPayload = {
  title: "",
  description: "",
  requirements: "",
  responsibilities: "",
  required_skills: [],
  preferred_skills: [],
  location: "",
  education_required: "",
  experience_required: 5,
  salary_min: 120000,
  salary_max: 160000,
  employment_type: "full-time",
  status: "draft",
};

export default function JobsPage() {
  const { user } = useAuth();
  const canManage = canManageJobs(user?.role);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [validationError, setValidationError] = useState("");
  const [form, setForm] = useState<CreateJobPayload>(emptyForm);
  const [requiredSkillsText, setRequiredSkillsText] = useState("");
  const [preferredSkillsText, setPreferredSkillsText] = useState("");
  const [createMode, setCreateMode] = useState<CreateMode>("structured");
  const [plainJobText, setPlainJobText] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [jobToDelete, setJobToDelete] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const validateCreateForm = (): string => {
    if (!canManage) return "Only admins can create jobs.";
    if (form.title.trim().length < 5) return "Title must be at least 5 characters.";
    if (form.description.trim().length < 50) return "Description must be at least 50 characters.";
    if (
      form.requirements &&
      form.requirements.trim().length > 0 &&
      form.requirements.trim().length < 50
    ) {
      return "Requirements must be at least 50 characters when provided.";
    }
    if (form.required_skills.length === 0) return "At least one required skill is needed.";
    if (
      form.salary_min !== null &&
      form.salary_max !== null &&
      form.salary_max < form.salary_min
    ) {
      return "Salary max must be greater than salary min.";
    }
    return "";
  };

  const loadJobs = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get<JobListResponse>("/api/jobs", {
        params: {
          page,
          page_size: pageSize,
          status_filter: statusFilter || undefined,
        },
      });
      setJobs(res.data.items);
      setTotalPages(res.data.total_pages || 1);
      setTotal(res.data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, page, pageSize]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  const submitCreateJob = async (targetStatus: "draft" | "active") => {
    const payload: CreateJobPayload = { ...form, status: targetStatus };
    const validation = validateCreateForm();
    if (validation) {
      setValidationError(validation);
      toast.error(validation);
      return;
    }
    setValidationError("");
    setSubmitting(true);
    setError("");

    try {
      await api.post<Job, CreateJobPayload>("/api/jobs", payload);
      setForm(emptyForm);
      setRequiredSkillsText("");
      setPreferredSkillsText("");
      toast.success(targetStatus === "active" ? "Job published" : "Draft saved");
      await loadJobs();
      setShowCreateForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create job");
      toast.error(err instanceof Error ? err.message : "Failed to create job");
    } finally {
      setSubmitting(false);
    }
  };

  const submitPlainTextJob = async (targetStatus: "draft" | "active") => {
    if (!canManage) {
      const msg = "Only admins can create jobs.";
      setValidationError(msg);
      toast.error(msg);
      return;
    }
    if (plainJobText.trim().length < 50) {
      const msg = "Pasted job description must be at least 50 characters.";
      setValidationError(msg);
      toast.error(msg);
      return;
    }

    setValidationError("");
    setSubmitting(true);
    setError("");
    try {
      await api.post("/api/jobs/from-text", {
        raw_text: plainJobText,
        status: targetStatus,
      });
      setPlainJobText("");
      toast.success(
        targetStatus === "active" ? "Job published and matching triggered" : "Draft saved"
      );
      await loadJobs();
      setShowCreateForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create job from text");
      toast.error(err instanceof Error ? err.message : "Failed to create job from text");
    } finally {
      setSubmitting(false);
    }
  };

  const onCreateJob = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await submitCreateJob("active");
  };

  const onDelete = async () => {
    if (!jobToDelete || !canManage) return;
    
    setIsDeleting(true);
    try {
      await api.delete(`/api/jobs/${jobToDelete}`);
      toast.success("Job deleted");
      setJobToDelete(null);
      await loadJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete job");
      toast.error(err instanceof Error ? err.message : "Failed to delete job");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="bg-[#fef8f3] min-h-screen p-8">
        {/* Main Content */} <div className="max-w-6xl mx-auto">
        
          {/* Top Bar */}
          {/* Replace the sticky top bar with this */}
 <div className="bg-white rounded-2xl border border-[#e8dfd6] px-6 py-5 mb-6">
  <div className="flex items-center justify-between">
    <div>
      <h1 className="text-xl font-bold text-[#1d1b19]">Jobs</h1>
      <p className="text-sm text-[#515f74]">
        {showCreateForm ? "Create a new job posting" : "Manage your job postings"}
      </p>
    </div>

    <div className="flex items-center gap-3">
      {showCreateForm ? (
        <button
          onClick={() => setShowCreateForm(false)}
          className="px-5 py-2 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg text-sm font-medium hover:bg-[#f8f3ee] transition-colors"
        >
          ← Back to Jobs
        </button>
      ) : (
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-5 py-2 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-lg text-sm font-semibold hover:shadow-lg transition-all"
        >
          + Create Job
        </button>
      )}
    </div>
  </div>
</div>
          {/* Content */}
          <div className="flex-1 overflow-auto p-8">
            {!showCreateForm ? (
              // ── Job List View ──
              <div className="space-y-6">
                 <div>
  <h2 className="text-2xl font-bold text-[#1d1b19] mb-1">Job List</h2>
</div>

                {error && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                    {error}
                  </div>
                )}
                {validationError && (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700">
                    {validationError}
                  </div>
                )}

                <div className="bg-white rounded-2xl overflow-hidden">
                  {/* Filter */}
                  <div className="px-8 py-4 border-b border-[#e8dfd6]">
                    <select
                      className="px-4 py-2 bg-[#f8f3ee] rounded-lg text-sm text-[#1d1b19] focus:outline-none focus:ring-2 focus:ring-[#3525cd]"
                      value={statusFilter}
                      onChange={(e) => {
                        setStatusFilter(e.target.value);
                        setPage(1);
                      }}
                    >
                      <option value="">All statuses</option>
                      <option value="draft">Draft</option>
                      <option value="active">Active</option>
                      <option value="paused">Paused</option>
                      <option value="closed">Closed</option>
                    </select>
                  </div>

                  {/* Table */}
                  <div className="overflow-x-auto">
                    {loading ? (
                      <div className="divide-y divide-[#e8dfd6]">
                        <SkeletonRow columns={4} />
                        <SkeletonRow columns={4} />
                        <SkeletonRow columns={4} />
                        <SkeletonRow columns={4} />
                        <SkeletonRow columns={4} />
                      </div>
                    ) : jobs.length === 0 ? (
                      <div className="p-8 text-center text-[#515f74]">No jobs found.</div>
                    ) : (
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-[#e8dfd6] bg-[#f8f3ee]">
                            <th className="px-8 py-4 text-left text-xs font-semibold text-[#515f74] uppercase">
                              Title
                            </th>
                            <th className="px-8 py-4 text-left text-xs font-semibold text-[#515f74] uppercase">
                              Status
                            </th>
                            <th className="px-8 py-4 text-left text-xs font-semibold text-[#515f74] uppercase">
                              Location
                            </th>
                            <th className="px-8 py-4 text-left text-xs font-semibold text-[#515f74] uppercase">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {jobs.map((job) => (
                            <tr
                              key={job.id}
                              className="border-b border-[#e8dfd6] hover:bg-[#fef8f3] transition-colors"
                            >
                              <td className="px-8 py-4 text-sm text-[#1d1b19] font-medium max-w-xs truncate">
                                {job.title || (job as any).job_title || "Untitled Job"}
                              </td>
                              <td className="px-8 py-4">
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
                              </td>
                              <td className="px-8 py-4 text-sm text-[#515f74]">
                                {job.location || "-"}
                              </td>
                              <td className="px-8 py-4 text-sm">
                                <div className="flex gap-2">
                                  <Link
                                    href={`/jobs/${job.id}`}
                                    className="text-[#3525cd] hover:underline font-medium"
                                  >
                                    View
                                  </Link>
                                  {canManage && (
                                    <button
                                      onClick={() => setJobToDelete(job.id)}
                                      className="text-[#7e3000] hover:underline font-medium"
                                    >
                                      Delete
                                    </button>
                                  )}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>

                  {/* Pagination */}
                  <div className="px-8 py-4 border-t border-[#e8dfd6] flex items-center justify-between">
                    <p className="text-sm text-[#515f74]">
                      Page {page} of {totalPages} ({total} jobs)
                    </p>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page <= 1}
                        className="px-4 py-2 text-sm font-medium text-[#515f74] hover:bg-[#f8f3ee] rounded-lg transition-colors disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <button
                        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                        disabled={page >= totalPages}
                        className="px-4 py-2 text-sm font-medium text-[#515f74] hover:bg-[#f8f3ee] rounded-lg transition-colors disabled:opacity-50"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              // ── Create Job View ──
              <div className="max-w-4xl">
                <div className="space-y-8">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-[#515f74] mb-2">JOBS</p>
                    <h2 className="text-4xl font-bold text-[#1d1b19]">
                      Build the <span className="text-[#3525cd]">perfect role</span> in minutes.
                    </h2>
                    <p className="text-[#515f74] mt-4">
                      Draft, publish, and trigger matching with confidence.
                    </p>
                  </div>

                  <div className="bg-white rounded-2xl p-8 space-y-8">
                    {/* Mode Tabs */}
                    <div className="flex gap-4 border-b border-[#e8dfd6]">
                      <button
                        onClick={() => setCreateMode("structured")}
                        className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                          createMode === "structured"
                            ? "border-[#3525cd] text-[#3525cd]"
                            : "border-transparent text-[#515f74] hover:text-[#1d1b19]"
                        }`}
                      >
                        Structured Form
                      </button>
                      <button
                        onClick={() => setCreateMode("plain_text")}
                        className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                          createMode === "plain_text"
                            ? "border-[#3525cd] text-[#3525cd]"
                            : "border-transparent text-[#515f74] hover:text-[#1d1b19]"
                        }`}
                      >
                        Paste Plain JD
                      </button>
                    </div>

                    {error && (
                      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                        {error}
                      </div>
                    )}
                    {validationError && (
                      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700">
                        {validationError}
                      </div>
                    )}
                    {!canManage && (
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-blue-700">
                        Read-only mode: only admins can create or delete jobs.
                      </div>
                    )}

                    {createMode === "structured" ? (
                      <form onSubmit={onCreateJob} className="space-y-6">
                        <div>
                          <label className="text-sm font-semibold text-[#1d1b19] block mb-2">
                            Job Title *
                          </label>
                          <input
                            type="text"
                            placeholder="Senior Python Developer"
                            className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                            value={form.title}
                            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                            required
                            minLength={5}
                            disabled={!canManage}
                          />
                        </div>

                        <div>
                          <label className="text-sm font-semibold text-[#1d1b19] block mb-2">
                            Description *
                          </label>
                          <textarea
                            placeholder="We're looking for an experienced Python developer..."
                            className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors resize-none disabled:opacity-50"
                            rows={4}
                            value={form.description}
                            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                            required
                            minLength={50}
                            disabled={!canManage}
                          />
                        </div>

                        <div>
                          <label className="text-sm font-semibold text-[#1d1b19] block mb-2">
                            Requirements *
                          </label>
                          <textarea
                            placeholder="5+ years Python experience, FastAPI, PostgreSQL, Docker, AWS..."
                            className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors resize-none disabled:opacity-50"
                            rows={4}
                            value={form.requirements}
                            onChange={(e) =>
                              setForm((f) => ({ ...f, requirements: e.target.value }))
                            }
                            minLength={50}
                            disabled={!canManage}
                          />
                        </div>

                        <div>
                          <label className="text-sm font-semibold text-[#1d1b19] block mb-2">
                            Required Skills (comma-separated) *
                          </label>
                          <input
                            type="text"
                            placeholder="Python, FastAPI, PostgreSQL, Docker, AWS"
                            className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                            value={requiredSkillsText}
                            onChange={(e) => {
                              const text = e.target.value;
                              setRequiredSkillsText(text);
                              setForm((f) => ({
                                ...f,
                                required_skills: text
                                  .split(",")
                                  .map((s) => s.trim())
                                  .filter(Boolean),
                              }));
                            }}
                            disabled={!canManage}
                          />
                        </div>

                        <div className="grid grid-cols-3 gap-4">
                          <div>
                            <label className="text-sm font-semibold text-[#1d1b19] block mb-2">
                              Location
                            </label>
                            <select
                              className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                              value={form.location}
                              onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
                              disabled={!canManage}
                            >
                              <option value="">Select location</option>
                              <option value="Remote">Remote</option>
                              <option value="San Francisco">San Francisco</option>
                              <option value="New York">New York</option>
                              <option value="Bangalore">Bangalore</option>
                            </select>
                          </div>
                          <div>
                            <label className="text-sm font-semibold text-[#1d1b19] block mb-2">
                              Experience (years)
                            </label>
                            <input
                              type="number"
                              min={0}
                              max={50}
                              className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                              value={form.experience_required ?? ""}
                              onChange={(e) =>
                                setForm((f) => ({
                                  ...f,
                                  experience_required: e.target.value
                                    ? Number(e.target.value)
                                    : null,
                                }))
                              }
                              disabled={!canManage}
                            />
                          </div>
                          <div>
                            <label className="text-sm font-semibold text-[#1d1b19] block mb-2">
                              Employment Type
                            </label>
                            <select
                              className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                              value={form.employment_type}
                              onChange={(e) =>
                                setForm((f) => ({
                                  ...f,
                                  employment_type: e.target.value as CreateJobPayload["employment_type"],
                                }))
                              }
                              disabled={!canManage}
                            >
                              <option value="full-time">Full-time</option>
                              <option value="part-time">Part-time</option>
                              <option value="contract">Contract</option>
                              <option value="internship">Internship</option>
                            </select>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="text-sm font-semibold text-[#1d1b19] block mb-2">
                              Salary Min
                            </label>
                            <input
                              type="number"
                              min={0}
                              className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                              value={form.salary_min ?? ""}
                              onChange={(e) =>
                                setForm((f) => ({
                                  ...f,
                                  salary_min: e.target.value ? Number(e.target.value) : null,
                                }))
                              }
                              disabled={!canManage}
                            />
                          </div>
                          <div>
                            <label className="text-sm font-semibold text-[#1d1b19] block mb-2">
                              Salary Max
                            </label>
                            <input
                              type="number"
                              min={0}
                              className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                              value={form.salary_max ?? ""}
                              onChange={(e) =>
                                setForm((f) => ({
                                  ...f,
                                  salary_max: e.target.value ? Number(e.target.value) : null,
                                }))
                              }
                              disabled={!canManage}
                            />
                          </div>
                        </div>

                        <div>
                          <label className="text-sm font-semibold text-[#1d1b19] block mb-2">
                            Preferred Skills (optional)
                          </label>
                          <input
                            type="text"
                            placeholder="React, Redis, Kubernetes"
                            className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                            value={preferredSkillsText}
                            onChange={(e) => {
                              const text = e.target.value;
                              setPreferredSkillsText(text);
                              setForm((f) => ({
                                ...f,
                                preferred_skills: text
                                  .split(",")
                                  .map((s) => s.trim())
                                  .filter(Boolean),
                              }));
                            }}
                            disabled={!canManage}
                          />
                        </div>

                        <div className="flex gap-4 pt-4">
                          <button
                            type="button"
                            disabled={submitting || !canManage}
                            onClick={() => submitCreateJob("draft")}
                            className="px-6 py-3 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg font-medium hover:bg-[#f8f3ee] transition-colors disabled:opacity-50"
                          >
                            {submitting ? "Saving..." : "Save as Draft"}
                          </button>
                          <button
                            type="submit"
                            disabled={submitting || !canManage}
                            className="px-6 py-3 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-lg font-medium hover:shadow-lg transition-all disabled:opacity-50"
                          >
                            {submitting ? "Publishing..." : "Publish & Find Matches →"}
                          </button>
                          <button
                            type="button"
                            onClick={() => setShowCreateForm(false)}
                            className="px-6 py-3 text-[#515f74] hover:bg-[#f8f3ee] rounded-lg font-medium transition-colors"
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    ) : (
                      <div className="space-y-6">
                        <div>
                          <label className="text-sm font-semibold text-[#1d1b19] block mb-2">
                            PASTE JOB DESCRIPTION *
                          </label>
                          <textarea
                            placeholder="Paste complete job description text here..."
                            className="w-full bg-[#f8f3ee] px-4 py-4 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors resize-none disabled:opacity-50"
                            rows={8}
                            value={plainJobText}
                            onChange={(e) => setPlainJobText(e.target.value)}
                            minLength={50}
                            disabled={!canManage}
                          />
                        </div>

                        <div className="flex gap-4">
                          <button
                            type="button"
                            disabled={submitting || !canManage}
                            onClick={() => submitPlainTextJob("draft")}
                            className="px-6 py-3 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg font-medium hover:bg-[#f8f3ee] transition-colors disabled:opacity-50"
                          >
                            {submitting ? "Saving..." : "Save as Draft"}
                          </button>
                          <button
                            type="button"
                            disabled={submitting || !canManage}
                            onClick={() => submitPlainTextJob("active")}
                            className="px-6 py-3 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-lg font-medium hover:shadow-lg transition-all disabled:opacity-50"
                          >
                            {submitting ? "Publishing..." : "Publish & Find Matches →"}
                          </button>
                          <button
                            type="button"
                            onClick={() => setShowCreateForm(false)}
                            className="px-6 py-3 text-[#515f74] hover:bg-[#f8f3ee] rounded-lg font-medium transition-colors"
                          >
                            Cancel
                          </button>
                        </div>

                        <p className="text-sm text-[#515f74] p-4 bg-[#f8f3ee] rounded-lg">
                          Parsed fields are extracted automatically. Published jobs trigger matching immediately.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      <Modal
        isOpen={!!jobToDelete}
        onClose={() => setJobToDelete(null)}
        title="Delete Job"
        primaryAction={{
          label: "Delete Job",
          onClick: onDelete,
          variant: "danger",
          loading: isDeleting,
        }}
        secondaryAction={{
          label: "Cancel",
          onClick: () => setJobToDelete(null),
        }}
      >
        <div className="space-y-3">
          <p className="text-sm text-[#1d1b19] font-medium">Are you sure you want to delete this job?</p>
          <p className="text-sm text-[#515f74]">
            This action cannot be undone. All candidate matches and data associated with this job will be permanently removed.
          </p>
        </div>
      </Modal>
    </ProtectedRoute>
  );
}