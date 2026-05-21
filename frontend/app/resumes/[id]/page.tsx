"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ProtectedRoute } from "@/lib/protected-route";
import api from "@/lib/api";
import { toast } from "sonner";
import "./resume.css";

type ResumeItem = {
  id: string;
  candidate_name: string;
  candidate_email: string | null;
  candidate_phone: string | null;
  file_name: string;
  file_type: string | null;
  skills: string[];
  experience_years: number | null;
  education: string | null;
  current_role: string | null;
  created_at: string;
  updated_at: string | null;
};

type CandidateMatch = {
  id: string;
  job_description_id: string;
  resume_id: string;
  overall_score: number;
  recruiter_status: string;
  created_at: string;
  job_title: string;
  job_status: string | null;
};

type CandidateMatchList = {
  items: CandidateMatch[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export default function ResumeDetailPage() {
  const params = useParams<{ id: string }>();
  const resumeId = params?.id;
  const [resume, setResume] = useState<ResumeItem | null>(null);
  const [matches, setMatches] = useState<CandidateMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!resumeId) return;
    const loadData = async () => {
      setLoading(true);
      setError("");
      try {
        const resumeRes = await api.get<ResumeItem>(`/api/resumes/${resumeId}`);
        setResume(resumeRes.data);

        try {
          const matchRes = await api.get<CandidateMatchList>("/api/matches/resume", {
            params: { resume_id: resumeId, page: 1, page_size: 20 },
          });
          setMatches(matchRes.data.items || []);
        } catch (matchErr) {
          console.error("Failed to load matches", matchErr);
          setMatches([]);
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Failed to load resume";
        const friendlyMsg =
          errorMsg.includes("image") || errorMsg.includes("model does not support")
            ? "Unable to load candidate data. Please try again."
            : errorMsg;
        setError(friendlyMsg);
        toast.error(friendlyMsg);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [resumeId]);

  const inferredLocation = useMemo(() => {
    if (!resume) return "Unknown";
    const blob = `${resume.current_role || ""} ${resume.education || ""} ${resume.candidate_name}`.toLowerCase();
    if (blob.includes("san francisco")) return "San Francisco, CA";
    if (blob.includes("new york")) return "New York, NY";
    if (blob.includes("remote")) return "Remote";
    if (blob.includes("bangalore") || blob.includes("bengaluru")) return "Bangalore, IN";
    return "Not specified";
  }, [resume]);

  const onView = async () => {
    if (!resumeId) {
      toast.error("Please sign in again");
      return;
    }

    try {
      const blob = await api.getBlob(`/api/resumes/${resumeId}/download`);
      const url = window.URL.createObjectURL(blob);
      const previewWindow = window.open(url, "_blank", "noopener,noreferrer");
      // Revoke after 60s to allow PDF to fully load in new tab
      setTimeout(() => window.URL.revokeObjectURL(url), 60000);
      if (!previewWindow) {
        toast.error("Popup blocked. Please allow popups or use Download.");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load PDF preview");
    }
  };

  const onDownload = async () => {
    if (!resumeId || !resume) {
      toast.error("No resume available");
      return;
    }

    try {
      const blob = await api.getBlob(`/api/resumes/${resumeId}/download`);
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = resume.file_name || "resume.pdf";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Download failed");
    }
  };

  const reanalyze = async () => {
    if (!resume) return;
    try {
      const res = await api.post(`/api/resumes/${resume.id}/re-analyze`, {});
      toast.success("Resume re-analyzed");
      setResume(res.data as typeof resume);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to re-analyze";
      toast.error(msg.includes("image") ? "Unable to analyze resume" : msg);
    }
  };

  return (
    <ProtectedRoute>
      <div className="resume-page">
        {/* LANDING PAGE MATCH NAV */}
        <nav className="resume-nav">
          <div className="nav-inner">
            <Link href="/dashboard" className="brand">
              <div className="brand-mark" />
              <span>AuraRecruiting</span>
            </Link>
            <div className="nav-actions">
              <Link href="/resumes" className="btn ghost">
                ← Back
              </Link>
            </div>
          </div>
        </nav>

        <main className="resume-shell">
          {error && <div className="alert error">{error}</div>}

          {loading ? (
            <div className="stack">
              <div className="card" style={{ height: "120px", background: "white", opacity: 0.5 }} />
              <div className="card" style={{ height: "400px", background: "white", opacity: 0.5 }} />
            </div>
          ) : !resume ? (
            <div className="muted text-center" style={{ marginTop: "100px" }}>Resume not found.</div>
          ) : (
            <>
              {/* PREMIUM HERO */}
              <header className="hero">
                <div>
                  <div className="eyebrow">Candidate Profile</div>
                  <h1>
                    {resume.candidate_name} <span>Verified</span>
                  </h1>
                  <p>{resume.current_role || "Professional"} · {inferredLocation}</p>
                </div>
                <div className="hero-actions">
                  <button onClick={onView} className="btn primary" type="button">
                    View PDF
                  </button>
                  <button onClick={onDownload} className="btn ghost" type="button">
                    Download
                  </button>
                </div>
              </header>

              {/* TWO COLUMN GRID */}
              <div className="grid-2">
                <div className="panel">
                  {/* CONTACT & SKILLS AREA */}
                  <div className="section-group">
                    <h3>Contact & Network</h3>
                    <div className="info-grid">
                      <Info
                        label="Email"
                        value={resume.candidate_email && resume.candidate_email !== "-" ? resume.candidate_email : "Not disclosed"}
                      />
                      <Info
                        label="Phone"
                        value={resume.candidate_phone && resume.candidate_phone !== "-" ? resume.candidate_phone : "Not provided"}
                      />
                      <Info
                        label="Location"
                        value={inferredLocation}
                      />
                    </div>
                  </div>

                  <div className="section-group">
                    <h3>Extracted Skills</h3>
                    {(!resume.skills || resume.skills.length === 0) ? (
                      <p className="card muted">No specific skills identified yet.</p>
                    ) : (
                      <div className="pill-row">
                        {resume.skills.map((skill, idx) => (
                          <span key={`${skill}-${idx}`} className="pill">
                            {skill}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="section-group">
                    <h3>Experience & Background</h3>
                    <div className="card">
                      <span className="strong">{resume.current_role || "Candidate"}</span>
                      <p className="muted">{resume.experience_years ?? 0} years professional experience</p>
                    </div>
                  </div>

                  <div className="section-group">
                    <h3>Education</h3>
                    <div className="card">
                      {formatEducation(resume.education) || (
                        <span className="muted italic">Education details not available.</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* SIDEBAR */}
                <aside className="sidebar-group">
                  <div className="section-group">
                    <h3>Resume File</h3>
                    <div className="card">
                      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
                        <div style={{ padding: "8px", background: "var(--res-indigo-soft)", borderRadius: "8px" }}>
                           📄
                        </div>
                        <div style={{ overflow: "hidden" }}>
                          <p className="strong" style={{ fontSize: "14px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {resume.file_name}
                          </p>
                          <p className="muted" style={{ fontSize: "11px" }}>Uploaded {timeAgo(resume.created_at)}</p>
                        </div>
                      </div>
                      <button onClick={reanalyze} className="btn ghost" style={{ width: "100%", fontSize: "12px" }}>
                        🔄 Refresh Analysis
                      </button>
                    </div>
                  </div>

                  <div className="section-group">
                    <h3>Job Matching ({matches.length})</h3>
                    <div className="timeline">
                      {matches.length === 0 ? (
                        <p className="card muted">No matches found.</p>
                      ) : (
                        matches.slice(0, 5).map((m) => {
                          const score = m.overall_score || 0;
                          const color = score > 80 ? "#10b981" : score > 60 ? "#f59e0b" : "#3525cd";
                          return (
                            <div key={m.id} className="card" style={{ padding: "16px" }}>
                              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                                <span className="strong" style={{ fontSize: "14px" }}>{m.job_title}</span>
                                <span style={{ color, fontWeight: 800, fontSize: "13px" }}>{score.toFixed(0)}%</span>
                              </div>
                              <div style={{ width: "100%", height: "4px", background: "#f0ece8", borderRadius: "10px", marginBottom: "12px" }}>
                                <div style={{ width: `${score}%`, height: "100%", background: color, borderRadius: "10px" }} />
                              </div>
                              <Link href={`/jobs/${m.job_description_id}`} className="btn ghost" style={{ width: "100%", padding: "6px", fontSize: "11px" }}>
                                View Match Details
                              </Link>
                            </div>
                          );
                        })
                      )}
                    </div>
                  </div>

                  <div className="section-group">
                    <h3>Recent Activity</h3>
                    <ul className="timeline">
                      <li>Profile created · {timeAgo(resume.created_at)}</li>
                      {matches.length > 0 && (
                        <li>Latest matching · {timeAgo(matches[0].created_at)}</li>
                      )}
                      <li>Current status · {latestStatus(matches)}</li>
                    </ul>
                  </div>
                </aside>
              </div>
            </>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="info-card">
      <p className="label">{label}</p>
      <p className="strong">{value}</p>
    </div>
  );
}

function timeAgo(iso: string): string {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "recently";
  const mins = Math.floor((Date.now() - t) / (1000 * 60));
  if (mins < 60) return `${Math.max(1, mins)}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days === 0) return "today";
  if (days === 1) return "yesterday";
  return `${days}d ago`;
}

function latestStatus(matches: CandidateMatch[]): string {
  if (matches.length === 0) return "New Profile";
  const status = (matches[0].recruiter_status || "new").toLowerCase();
  if (status === "shortlisted") return "Shortlisted";
  if (status === "rejected") return "Rejected";
  if (status === "interviewed") return "Interviewing";
  if (status === "offered") return "Offered";
  return "Reviewed";
}

function formatEducation(raw: string | null): string {
  if (!raw) return "";

  try {
    const parsed = JSON.parse(raw);

    // Helper to extract degree from an object or string
    const extract = (item: any): string => {
      if (!item) return "";
      // If the item is itself a JSON string (double-encoded), parse it
      if (typeof item === "string") {
        try {
          const inner = JSON.parse(item);
          return inner?.degree ? String(inner.degree) : item;
        } catch {
          return item;
        }
      }
      if (typeof item === "object" && item?.degree) {
        return String(item.degree);
      }
      return String(item);
    };

    // Case 1: plain object { degree: "..." }
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed) && "degree" in parsed) {
      return String(parsed.degree);
    }

    // Case 2: array
    if (Array.isArray(parsed)) {
      return parsed
        .map(extract)
        .filter(Boolean)
        .join(" | ");
    }
  } catch {
    // Not JSON
  }

  return raw;
}