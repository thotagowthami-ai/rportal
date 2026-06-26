"use client";
import { getApiUrl } from "../../api";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import api from "@/lib/api";
import { ProtectedRoute } from "@/lib/protected-route";
import { toast } from "sonner";
import { Modal } from "@/components/ui/Modal";

type Candidate = {
  id: string;
  candidate_name: string;
  current_role: string;
  experience_years: number;
  education: string;
  skills: string[];
  file_name?: string;
  created_at: string;
};

type ResumesResponse = Candidate[] | { items?: Candidate[]; results?: Candidate[] };

// Helper function to parse and clean education field
const parseEducation = (educationString: string | null | undefined): string => {
  if (!educationString) return "";
  
  try {
    // Try to parse as JSON
    const parsed = JSON.parse(educationString);
    if (typeof parsed === "object" && parsed.degree) {
      return parsed.degree;
    }
    return educationString;
  } catch (e) {
    // If it's not valid JSON, return as-is
    return educationString;
  }
};

export default function ResumesPage() {
  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");
  const [candidatePhone, setCandidatePhone] = useState("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadMessage, setUploadMessage] = useState("");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [candidateToDelete, setCandidateToDelete] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const loadCandidates = async () => {
      try {
        setLoading(true);
        const res = await api.get<ResumesResponse>("/api/resumes");
        const list = Array.isArray(res.data)
          ? res.data
          : Array.isArray(res.data.items)
          ? res.data.items
          : Array.isArray((res.data as { results?: Candidate[] }).results)
          ? (res.data as { results?: Candidate[] }).results!
          : [];
        setCandidates(list);
      } catch (err) {
        console.error("Failed to load candidates", err);
        setCandidates([]);
      } finally {
        setLoading(false);
      }
    };
    void loadCandidates();
  }, []);

  const onSyncPortal = async () => {
    try {
      setLoading(true);
      const res = await api.post<{ message: string; count: number }>("/api/resumes/sync", {});
      toast.success(res.data.message);
      // Reload candidates
      const listRes = await api.get<ResumesResponse>("/api/resumes");
      const list = Array.isArray(listRes.data)
        ? listRes.data
        : Array.isArray(listRes.data.items)
        ? listRes.data.items
        : Array.isArray((listRes.data as { results?: Candidate[] }).results)
        ? (listRes.data as { results?: Candidate[] }).results!
        : [];
      setCandidates(list);
    } catch (err) {
      console.error("Sync failed", err);
      toast.error("Failed to sync from portal");
    } finally {
      setLoading(false);
    }
  };

  const onUpload = async () => {
    if (selectedFiles.length === 0) {
      setUploadMessage("Please select at least one file.");
      return;
    }

    if (
      selectedFiles.length > 1 &&
      (candidateName || candidateEmail || candidatePhone)
    ) {
      setUploadMessage("Candidate details can only be used with a single resume upload.");
      return;
    }

    setUploadMessage("Uploading...");
    const formData = new FormData();
    selectedFiles.forEach((file) => formData.append("files", file));

    if (candidateName) formData.append("candidate_name", candidateName);
    if (candidateEmail) formData.append("candidate_email", candidateEmail);
    if (candidatePhone) formData.append("candidate_phone", candidatePhone);

    try {
      await api.postForm("/api/resumes/upload-multiple", formData);
      setUploadMessage("Upload complete!");
      setSelectedFiles([]);
      const res = await api.get<ResumesResponse>("/api/resumes");
      const list = Array.isArray(res.data)
        ? res.data
        : Array.isArray(res.data.items)
        ? res.data.items
        : Array.isArray((res.data as { results?: Candidate[] }).results)
        ? (res.data as { results?: Candidate[] }).results!
        : [];
      setCandidates(list);
    } catch {
      setUploadMessage("Upload failed. Please try again.");
    }
  };
  const downloadResume = async (resumeId: string, fileName: string) => {
    try {
      const tokenRes = await api.post<{ download_token: string }>(`/api/resumes/${resumeId}/download-token`, {});
      const downloadUrl = `${getApiUrl() ?? ""}/api/resumes/${resumeId}/download?token=${tokenRes.data.download_token}&download=true`;
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = fileName || "resume.pdf";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (err: any) {
      console.error("Download error:", err);
      const errMsg = err instanceof Error ? err.message : "";
      if (errMsg.includes("404") || errMsg.toLowerCase().includes("not found")) {
        toast.error("Resume file is missing from the server (wiped during redeployment). Please re-upload this candidate's resume.");
      } else {
        toast.error("Failed to download resume. Please try again.");
      }
    }
  };
  

  const deleteCandidate = async () => {
    if (!candidateToDelete) return;
    setIsDeleting(true);
    try {
      await api.delete(`/api/resumes/${candidateToDelete}`);
      setCandidates((prev) => prev.filter((c) => c.id !== candidateToDelete));
      toast.success("Candidate deleted");
      setCandidateToDelete(null);
    } catch (err) {
      console.error("Delete failed", err);
      toast.error("Failed to delete candidate");
    } finally {
      setIsDeleting(false);
    }
  };

  const filtered = candidates.filter(
    (c) =>
      c.candidate_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.skills?.some((s) => s.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <ProtectedRoute>
      <div className="bg-[#fef8f3] min-h-screen p-8">
        <div className="max-w-5xl mx-auto space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-[#1d1b19]">Candidates</h1>
              <p className="text-sm text-[#515f74]">
                Upload and manage candidate resumes
              </p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onSyncPortal}
                disabled={loading}
                className="px-5 py-2 bg-white border border-[#e8dfd6] text-[#3525cd] rounded-lg text-sm font-semibold hover:bg-[#fef8f3] transition-all flex items-center gap-2"
              >
                <span>🔄</span> {loading ? "Syncing..." : "Sync Portal"}
              </button>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="px-5 py-2 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-lg text-sm font-semibold hover:shadow-lg transition-all"
              >
                + Upload Resume
              </button>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6">
            <div className="mb-5">
              <h2 className="text-base font-bold text-[#1d1b19]">Candidate Details</h2>
              <p className="text-sm text-[#515f74]">Optional — enriches uploaded resumes</p>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <input
                type="text"
                placeholder="Candidate name (optional)"
                value={candidateName}
                onChange={(e) => setCandidateName(e.target.value)}
                className="bg-[#f8f3ee] px-4 py-2.5 rounded-lg text-sm text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors"
              />
              <input
                type="email"
                placeholder="Candidate email (optional)"
                value={candidateEmail}
                onChange={(e) => setCandidateEmail(e.target.value)}
                className="bg-[#f8f3ee] px-4 py-2.5 rounded-lg text-sm text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors"
              />
              <input
                type="tel"
                placeholder="Candidate phone (optional)"
                value={candidatePhone}
                onChange={(e) => setCandidatePhone(e.target.value)}
                className="bg-[#f8f3ee] px-4 py-2.5 rounded-lg text-sm text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors"
              />
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6">
            <div className="mb-5">
              <h2 className="text-base font-bold text-[#1d1b19]">Upload Resumes</h2>
              <p className="text-sm text-[#515f74]">PDF, DOC, DOCX — up to 10 MB each</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-[#e8dfd6] rounded-xl p-8 flex flex-col items-center justify-center gap-3 cursor-pointer hover:border-[#3525cd] hover:bg-[#fef8f3] transition-colors"
              >
                <div className="w-12 h-12 bg-[#f8f3ee] rounded-full flex items-center justify-center text-2xl">
                  📄
                </div>
                <p className="text-sm font-semibold text-[#1d1b19]">Drag & drop files here</p>
                <p className="text-xs text-[#515f74]">or click to browse</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.doc,.docx"
                  multiple
                  className="hidden"
                  onChange={(e) => setSelectedFiles(Array.from(e.target.files || []))}
                />
              </div>

              <div className="bg-[#f8f3ee] rounded-xl p-5 flex flex-col justify-between">
                <div>
                  <p className="text-sm font-bold text-[#1d1b19] mb-2">
                    Selected Files ({selectedFiles.length})
                  </p>
                  <p className="text-sm text-[#515f74] leading-relaxed">
                    {selectedFiles.length > 0
                      ? selectedFiles.map((f) => f.name).join(", ")
                      : "No files selected yet."}
                  </p>
                  {uploadMessage && (
                    <span
                      className={
                        uploadMessage.includes("complete")
                          ? "inline-block mt-3 text-xs font-semibold text-green-600 bg-green-50 px-3 py-1 rounded-full"
                          : uploadMessage.includes("failed")
                          ? "inline-block mt-3 text-xs font-semibold text-red-500 bg-red-50 px-3 py-1 rounded-full"
                          : "inline-block mt-3 text-xs font-semibold text-[#3525cd] bg-[#3525cd]/10 px-3 py-1 rounded-full"
                      }
                    >
                      {uploadMessage}
                    </span>
                  )}
                </div>
                <div className="flex gap-2 mt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedFiles([]);
                      setUploadMessage("");
                      fileInputRef.current?.click();
                    }}
                    className="flex-1 px-4 py-2 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg text-sm font-medium hover:bg-white transition-colors"
                  >
                    Browse More
                  </button>
                  <button
                    type="button"
                    onClick={onUpload}
                    className="flex-1 px-4 py-2 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-lg text-sm font-semibold hover:shadow-lg transition-all"
                  >
                    Upload
                  </button>
                </div>
              </div>
            </div>

            <p className="text-xs text-[#515f74] mt-3">
              AI parses skills, experience, and education automatically.
            </p>
          </div>

          <div className="bg-white rounded-2xl p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
  <h2 className="text-base font-bold text-[#1d1b19]">
    Candidates ({candidates.length})
  </h2>
                <p className="text-sm text-[#515f74]">All uploaded candidate profiles</p>
              </div>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg text-sm font-medium hover:bg-[#f8f3ee] transition-colors"
              >
                + Upload More
              </button>
            </div>

            <div className="mb-4">
              <input
                type="text"
                placeholder="Search by name or skill..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#f8f3ee] px-4 py-2.5 rounded-lg text-sm text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors"
              />
            </div>

            <div className="space-y-3">
              {loading ? (
                [1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-20 bg-[#f8f3ee] rounded-xl animate-pulse"
                  />
                ))
              ) : filtered.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 gap-3">
                  <div className="w-14 h-14 bg-[#f8f3ee] rounded-full flex items-center justify-center text-3xl">
                    👤
                  </div>
                  <p className="text-sm font-semibold text-[#1d1b19]">No candidates yet</p>
                  <p className="text-xs text-[#515f74]">Upload a resume above to get started.</p>
                </div>
              ) : (
                filtered.map((c) => (
                  <div
                    key={c.id}
                    className="flex items-center gap-4 px-4 py-4 bg-[#f8f3ee] rounded-xl hover:bg-[#f3ede6] transition-colors"
                  >
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white font-bold text-sm flex items-center justify-center flex-shrink-0">
                      {c.candidate_name?.charAt(0)?.toUpperCase() || "?"}
                    </div>

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-[#1d1b19] mb-0.5">
                        {c.candidate_name}
                      </p>
                      <p className="text-xs text-[#515f74] mb-1.5">
                        {[
                          c.current_role,
                          c.experience_years != null && `${c.experience_years}y exp`,
                          parseEducation(c.education),
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                      </p>
                      {c.skills?.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {c.skills.slice(0, 5).map((s) => (
                            <span
                              key={s}
                              className="px-2 py-0.5 bg-[#3525cd]/10 text-[#3525cd] rounded-full text-xs font-medium"
                            >
                              {s}
                            </span>
                          ))}
                          {c.skills.length > 5 && (
                            <span className="px-2 py-0.5 bg-[#3525cd]/10 text-[#3525cd] rounded-full text-xs font-medium">
                              +{c.skills.length - 5}
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2 flex-shrink-0">
                          <Link
                            href={`/resumes/${c.id}`}
                            className="px-3 py-1.5 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg text-xs font-medium hover:bg-white transition-colors"
                          >
                            View →
                          </Link>
                      <button
                        type="button"
                        onClick={() => downloadResume(c.id, c.file_name ?? "resume.pdf")}
                        className="px-3 py-1.5 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg text-xs font-medium hover:bg-white transition-colors"
                      >
                        Download
                      </button>
                      <button
                        type="button"
                        onClick={() => setCandidateToDelete(c.id)}
                        className="px-3 py-1.5 bg-white border border-red-200 text-red-500 rounded-lg text-xs font-medium hover:bg-red-50 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
      <Modal
        isOpen={!!candidateToDelete}
        onClose={() => setCandidateToDelete(null)}
        title="Delete Candidate"
        primaryAction={{
          label: "Delete Candidate",
          onClick: deleteCandidate,
          variant: "danger",
          loading: isDeleting,
        }}
        secondaryAction={{
          label: "Cancel",
          onClick: () => setCandidateToDelete(null),
        }}
      >
        <div className="space-y-3">
          <p className="text-sm text-[#1d1b19] font-medium">Are you sure you want to delete this candidate?</p>
          <p className="text-sm text-[#515f74]">
            This action cannot be undone. All resume analysis, matching scores, and associated candidate records will be permanently removed.
          </p>
        </div>
      </Modal>
    </ProtectedRoute>
  );
}
