"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";

type Resume = {
  id: string;
  candidate_name: string;
  file_name: string;
  email: string | null;
  candidate_email: string | null;
  phone: string | null;
  candidate_phone: string | null;
  phone_number: string | null;
  linkedin: string | null;
  linkedin_url: string | null;
  location: string | null;
  summary: string | null;
  skills: string[];
  experience_years: number | null;
  education: string | null;
  work_experience: { company: string; role: string; duration: string }[] | null;
  created_at: string;
};

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

type MatchItem = {
  id: string;
  job_description_id: string;
  overall_score: number;
  skill_match_score: number | null;
  recruiter_status: string;
  match_reasoning: string | null;
  matched_skills: string[] | null;
  missing_skills: string[] | null;
  created_at: string;
};

type JobItem = {
  id: string;
  title: string;
  status: string;
  location: string | null;
};

export default function CandidateProfilePage() {
  const params = useParams<{ id: string }>();
  const candidateId = params?.id;

  const [resume, setResume] = useState<Resume | null>(null);
  const [matches, setMatches] = useState<MatchItem[]>([]);
  const [jobs, setJobs] = useState<Record<string, JobItem>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"profile" | "matches">("profile");
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailSubject, setEmailSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");

  useEffect(() => {
    if (!candidateId) return;
    (async () => {
      setError("");
      setResume(null);
      setMatches([]);
      setJobs({});
      setLoading(true);
      try {
        const resumeRes = await api.get<Resume>(`/api/resumes/${candidateId}`);
        setResume(resumeRes.data);
        try {
          const matchRes = await api.get<{ items: MatchItem[] }>("/api/matches/resume", {
            params: { resume_id: candidateId, page: 1, page_size: 50 },
          });
          const matchItems = matchRes.data.items || [];
          setMatches(matchItems);
          const jobIds = [...new Set(matchItems.map((m) => m.job_description_id))];
          const jobEntries: Record<string, JobItem> = {};
          await Promise.all(
            jobIds.map(async (jid) => {
              try {
                const jr = await api.get<JobItem>(`/api/jobs/${jid}`);
                jobEntries[jid] = jr.data;
              } catch {
                jobEntries[jid] = { id: jid, title: "Unknown Job", status: "unknown", location: null };
              }
            })
          );
          setJobs(jobEntries);
        } catch {
          setMatches([]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load candidate");
      } finally {
        setLoading(false);
      }
    })();
  }, [candidateId]);

  const email = resume?.email || resume?.candidate_email;
  const phone = resume?.phone || resume?.candidate_phone || resume?.phone_number;
  const linkedin = resume?.linkedin || resume?.linkedin_url;

  if (loading) {
    return (
      <div className="min-h-screen bg-[#fdf8f3] font-sans">
        <nav className="fixed top-0 left-0 right-0 z-50 h-14 flex items-center justify-between px-10 bg-[rgba(253,248,243,0.92)] backdrop-blur-2xl border-b border-[rgba(232,223,214,0.6)]">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#3525cd]" />
            <span className="text-sm font-extrabold text-[#1d1b19]">AuraRecruiting</span>
          </div>
        </nav>
        <main className="pt-20 pb-20 px-6 max-w-5xl mx-auto">
          <div className="space-y-4">
            <div className="h-8 bg-[#f8f3ee] rounded animate-pulse w-2/3" />
            <div className="h-4 bg-[#f8f3ee] rounded animate-pulse w-1/3" />
            <div className="h-24 bg-[#f8f3ee] rounded animate-pulse" />
          </div>
        </main>
      </div>
    );
  }

  if (error || !resume) {
    return (
      <div className="min-h-screen bg-[#fdf8f3] font-sans">
        <nav className="fixed top-0 left-0 right-0 z-50 h-14 flex items-center justify-between px-10 bg-[rgba(253,248,243,0.92)] backdrop-blur-2xl border-b border-[rgba(232,223,214,0.6)]">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#3525cd]" />
            <span className="text-sm font-extrabold text-[#1d1b19]">AuraRecruiting</span>
          </div>
          <Link href="/resumes" className="text-[0.85rem] font-medium text-[#515f74] hover:text-[#1d1b19]">
            ← Back to Candidates
          </Link>
        </nav>
        <main className="pt-32 pb-20 px-6 max-w-5xl mx-auto text-center">
          <div className="text-5xl mb-4">😕</div>
          <h1 className="text-3xl font-extrabold text-[#1d1b19] mb-3">Candidate Not Found</h1>
          <p className="text-[#515f74] mb-6">{error || "This profile does not exist."}</p>
          <Link href="/resumes" className="inline-flex items-center gap-2 text-[0.9rem] font-bold text-white px-7 py-3 rounded-lg bg-[#3525cd] hover:bg-[#4f46e5]">
            ← Back to Candidates
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#fdf8f3] font-sans">
      {/* Email Modal */}
      {showEmailModal && email && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShowEmailModal(false)}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-[#f8f3ee]">
              <div className="text-[0.68rem] font-bold text-[#3525cd] uppercase tracking-widest mb-1">Compose Email</div>
              <h2 className="text-xl font-bold text-[#1d1b19]">Contact {resume.candidate_name}</h2>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="text-[0.85rem] font-semibold text-[#1d1b19] block mb-2">To</label>
                <input className="w-full px-3 py-2 border border-[#e8dfd6] rounded-lg bg-white text-[#1d1b19]" type="email" value={email} readOnly />
              </div>
              <div>
                <label className="text-[0.85rem] font-semibold text-[#1d1b19] block mb-2">Subject</label>
                <input className="w-full px-3 py-2 border border-[#e8dfd6] rounded-lg bg-white text-[#1d1b19]" type="text" value={emailSubject} onChange={(e) => setEmailSubject(e.target.value)} placeholder="Subject line..." />
              </div>
              <div>
                <label className="text-[0.85rem] font-semibold text-[#1d1b19] block mb-2">Message</label>
                <textarea className="w-full px-3 py-2 border border-[#e8dfd6] rounded-lg bg-white text-[#1d1b19]" rows={6} value={emailBody} onChange={(e) => setEmailBody(e.target.value)} placeholder="Write your message..." />
              </div>
            </div>
            <div className="px-6 py-4 border-t border-[#f8f3ee] flex gap-3">
              <button className="flex-1 px-4 py-2 rounded-lg border border-[#e8dfd6] text-[#1d1b19] font-semibold hover:bg-[#f8f3ee]" onClick={() => setShowEmailModal(false)}>
                Cancel
              </button>
              <a className="flex-1 px-4 py-2 rounded-lg bg-[#3525cd] text-white font-semibold hover:bg-[#4f46e5] text-center" href={`mailto:${email}?subject=${encodeURIComponent(emailSubject)}&body=${encodeURIComponent(emailBody)}`} onClick={() => setShowEmailModal(false)}>
                ✉ Send Email
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 h-14 flex items-center justify-between px-10 bg-[rgba(253,248,243,0.92)] backdrop-blur-2xl border-b border-[rgba(232,223,214,0.6)]">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[#3525cd]" />
          <span className="text-sm font-extrabold text-[#1d1b19]">AuraRecruiting</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/resumes" className="text-[0.85rem] font-medium text-[#515f74] hover:text-[#1d1b19]">
            ← Candidates
          </Link>
          {email && <a href={`mailto:${email}`} className="text-[0.85rem] font-medium text-[#515f74] hover:text-[#1d1b19]">✉ Email</a>}
          <Link href="/dashboard" className="text-[0.825rem] font-bold text-white px-5 py-2 rounded-full bg-[#3525cd] hover:bg-[#4f46e5]">
            Dashboard
          </Link>
        </div>
      </nav>

      <main className="pt-24 pb-20 px-6 max-w-5xl mx-auto">
        {/* Hero Section */}
        <div className="bg-white rounded-2xl border border-[#e8dfd6] shadow-[0_4px_24px_rgba(0,0,0,0.07)] p-8 mb-8">
          <div className="flex items-start justify-between gap-8 mb-6">
            <div className="flex-1">
              <div className="text-[0.68rem] font-bold text-[#3525cd] uppercase tracking-widest mb-3">Candidate Profile</div>
              <h1 className="text-[clamp(1.2rem,2vw,1.8rem)] font-extrabold text-[#1d1b19] leading-tight mb-2">
                {resume.candidate_name}
                {resume.experience_years != null && <span className="text-[#3525cd]"> · {resume.experience_years}y exp</span>}
              </h1>
              <p className="text-[#515f74] text-[0.975rem] leading-relaxed mb-6 max-w-2xl">
                {resume.summary || resume.file_name}
              </p>

              {/* Contact Info Chips */}
              <div className="flex flex-wrap gap-3 mb-8">
                {resume.location && (
                  <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#fdf8f3] border border-[#f8f3ee] text-[#515f74] text-[0.85rem] font-medium">
                    📍 {resume.location}
                  </div>
                )}
                {email && (
                  <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#fdf8f3] border border-[#f8f3ee] text-[#515f74] text-[0.85rem] font-medium">
                    ✉ {email}
                  </div>
                )}
                {phone && (
                  <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#fdf8f3] border border-[#f8f3ee] text-[#515f74] text-[0.85rem] font-medium">
                    📞 {phone}
                  </div>
                )}
                {linkedin && (
                  <a href={linkedin} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#fdf8f3] border border-[#f8f3ee] text-[#515f74] text-[0.85rem] font-medium hover:bg-white hover:border-[#e8dfd6] transition-all">
                    🔗 LinkedIn
                  </a>
                )}
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#fdf8f3] border border-[#f8f3ee] text-[#515f74] text-[0.85rem] font-medium">
                  🎯 {matches.length} match{matches.length !== 1 ? "es" : ""}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-3">
                {email ? (
                  <button className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-[#3525cd] text-white font-bold hover:bg-[#4f46e5] transition-all hover:-translate-y-0.5" onClick={() => {
                    setEmailSubject(`Opportunity for ${resume.candidate_name}`);
                    setEmailBody(`Hi ${resume.candidate_name},\n\nI came across your profile and would love to connect regarding an exciting opportunity.\n\nBest regards`);
                    setShowEmailModal(true);
                  }}>
                    ✉ Contact via Email
                  </button>
                ) : (
                  <button className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-[#f8f3ee] text-[#515f74] font-bold cursor-not-allowed opacity-50" disabled>
                    ✉ No Email
                  </button>
                )}

                {email && (
                  <a className="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-[#e8dfd6] bg-white text-[#1d1b19] font-bold hover:bg-[#fdf8f3] transition-all hover:-translate-y-0.5" href={`https://calendar.google.com/calendar/render?action=TEMPLATE&text=Interview+with+${encodeURIComponent(resume.candidate_name)}&details=${encodeURIComponent(`Interview scheduled with ${resume.candidate_name}${email ? ` (${email})` : ""}`)}&add=${encodeURIComponent(email)}`} target="_blank" rel="noopener noreferrer">
                    📅 Schedule Interview
                  </a>
                )}

                {phone && (
                  <a className="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-[#e8dfd6] bg-white text-[#1d1b19] font-bold hover:bg-[#fdf8f3] transition-all hover:-translate-y-0.5" href={`tel:${phone}`}>
                    📞 Call
                  </a>
                )}

                {linkedin && (
                  <a className="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-[#e8dfd6] bg-white text-[#1d1b19] font-bold hover:bg-[#fdf8f3] transition-all hover:-translate-y-0.5" href={linkedin} target="_blank" rel="noopener noreferrer">
                    🔗 LinkedIn
                  </a>
                )}

                <button className="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-[#e8dfd6] bg-white text-[#1d1b19] font-bold hover:bg-[#fdf8f3] transition-all hover:-translate-y-0.5" onClick={async () => {
                  try {
                    await api.post(`/api/resumes/${resume.id}/re-analyze`, {});
                    alert("Resume re-analysis started. Please check back in a moment.");
                  } catch (err) {
                    alert("Failed to re-analyze resume. Please try again.");
                  }
                }}>
                  🔄 Reanalyze
                </button>

                <button className="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-[#e8dfd6] bg-white text-[#1d1b19] font-bold hover:bg-[#fdf8f3] transition-all hover:-translate-y-0.5" onClick={async () => {
                  try {
                    const blob = await api.getBlob(`/api/resumes/${resume.id}/download`);
                    const url = window.URL.createObjectURL(blob);
                    const newTab = window.open(url, '_blank');
                    // Revoke after 60s to allow PDF to fully load in new tab
                    setTimeout(() => window.URL.revokeObjectURL(url), 60000);
                    if (!newTab) {
                      alert("Popup blocked. Please allow popups for this site and try again.");
                    }
                  } catch (err: unknown) {
                    const errorMsg = err instanceof Error ? err.message : "Failed to view PDF";
                    alert(errorMsg.includes("missing") ? `Resume file is missing. Please re-upload the resume.` : "Failed to view PDF. Please try again.");
                  }
                }}>
                  📄 View PDF
                </button>

                <button className="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-[#e8dfd6] bg-white text-[#1d1b19] font-bold hover:bg-[#fdf8f3] transition-all hover:-translate-y-0.5" onClick={async () => {
                  try {
                    const blob = await api.getBlob(`/api/resumes/${resume.id}/download`);
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = resume.file_name || "resume.pdf";
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                  } catch (err: unknown) {
                    const errorMsg = err instanceof Error ? err.message : "Failed to download resume";
                    alert(errorMsg.includes("missing") ? `Resume file is missing. Please re-upload the resume.` : "Failed to download resume. Please try again.");
                  }
                }}>
                  ⬇️ Download
                </button>
              </div>
            </div>

            {/* Avatar */}
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-[#3525cd] to-[#4f46e5] flex items-center justify-center flex-shrink-0 hidden md:flex">
              <span className="text-3xl font-extrabold text-white">{resume.candidate_name.charAt(0).toUpperCase()}</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-8 border-b border-[#f8f3ee]">
          <button className={`px-6 py-4 font-bold text-[0.95rem] transition-all border-b-2 ${activeTab === "profile" ? "text-[#3525cd] border-[#3525cd]" : "text-[#515f74] border-transparent hover:text-[#1d1b19]"}`} onClick={() => setActiveTab("profile")}>
            Profile
          </button>
          <button className={`px-6 py-4 font-bold text-[0.95rem] transition-all border-b-2 flex items-center gap-2 ${activeTab === "matches" ? "text-[#3525cd] border-[#3525cd]" : "text-[#515f74] border-transparent hover:text-[#1d1b19]"}`} onClick={() => setActiveTab("matches")}>
            Job Matches
            {matches.length > 0 && <span className="bg-[#3525cd] text-white px-2 py-1 rounded-full text-[0.7rem] font-bold">{matches.length}</span>}
          </button>
        </div>

        {/* Profile Tab */}
        {activeTab === "profile" && (
          <div className="space-y-6">
            {resume.skills && resume.skills.length > 0 && (
              <div className="bg-white rounded-2xl border border-[#e8dfd6] p-8">
                <h3 className="text-[0.68rem] font-bold text-[#3525cd] uppercase tracking-widest mb-6">Skills</h3>
                <div className="flex flex-wrap gap-3">
                  {resume.skills.map((skill) => (
                    <span key={skill} className="px-4 py-2 rounded-full bg-[#fdf8f3] border border-[#f8f3ee] text-[#3525cd] text-[0.85rem] font-semibold">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-white rounded-2xl border border-[#e8dfd6] p-8">
              <div className="grid md:grid-cols-4 gap-8">
                {resume.education && (
                  <div>
                    <div className="text-[0.68rem] font-bold text-[#3525cd] uppercase tracking-widest mb-2">Education</div>
                    <div className="text-[1.1rem] font-bold text-[#1d1b19]">{parseEducation(resume.education)}</div>
                  </div>
                )}
                <div>
                  <div className="text-[0.68rem] font-bold text-[#3525cd] uppercase tracking-widest mb-2">Experience</div>
                  <div className="text-[1.1rem] font-bold text-[#1d1b19]">{resume.experience_years != null ? `${resume.experience_years} years` : "Not specified"}</div>
                </div>
                <div>
                  <div className="text-[0.68rem] font-bold text-[#3525cd] uppercase tracking-widest mb-2">Source File</div>
                  <div className="text-[0.95rem] font-semibold text-[#515f74]">📄 {resume.file_name}</div>
                </div>
                <div>
                  <div className="text-[0.68rem] font-bold text-[#3525cd] uppercase tracking-widest mb-2">Added</div>
                  <div className="text-[0.95rem] font-semibold text-[#515f74]">{new Date(resume.created_at).toLocaleDateString()}</div>
                </div>
              </div>
            </div>

            {resume.work_experience && resume.work_experience.length > 0 && (
              <div className="bg-white rounded-2xl border border-[#e8dfd6] p-8">
                <h3 className="text-[0.68rem] font-bold text-[#3525cd] uppercase tracking-widest mb-6">Work Experience</h3>
                <div className="space-y-4">
                  {resume.work_experience.map((exp, i) => (
                    <div key={i} className="flex gap-4 pb-4 border-b border-[#f8f3ee] last:border-b-0">
                      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-[#3525cd] to-[#4f46e5] flex items-center justify-center flex-shrink-0 text-white font-bold text-lg">
                        {exp.company?.charAt(0) || "?"}
                      </div>
                      <div className="flex-1">
                        <div className="font-bold text-[#1d1b19] mb-1">{exp.role}</div>
                        <div className="text-[#515f74] text-[0.9rem] mb-1">{exp.company}</div>
                        {exp.duration && <div className="text-[#515f74] text-[0.85rem]">{exp.duration}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Matches Tab */}
        {activeTab === "matches" && (
          <div className="space-y-6">
            {matches.length === 0 ? (
              <div className="bg-white rounded-2xl border border-[#e8dfd6] p-16 text-center">
                <div className="text-5xl mb-4">🎯</div>
                <h2 className="text-2xl font-bold text-[#1d1b19] mb-2">No Matches Yet</h2>
                <p className="text-[#515f74]">This candidate hasn't been matched to any jobs yet.</p>
              </div>
            ) : (
              [...matches]
                .sort((a, b) => b.overall_score - a.overall_score)
                .map((match, idx) => {
                  const job = jobs[match.job_description_id];
                  const score = Math.min(100, Math.max(0, match.overall_score));
                  const scoreColor = score >= 75 ? "#16a34a" : score >= 50 ? "#d97706" : "#dc2626";

                  return (
                    <div key={match.id} className="bg-white rounded-2xl border border-[#e8dfd6] p-8">
                      <div className="flex items-start justify-between gap-6 mb-6 flex-wrap">
                        <div>
                          <div className="text-[0.68rem] font-bold text-[#3525cd] uppercase tracking-widest mb-2">Match #{idx + 1}</div>
                          <h3 className="text-xl font-bold text-[#1d1b19] mb-2">{job?.title || "Unknown Job"}</h3>
                          {job?.location && <div className="text-[#515f74] text-[0.9rem]">📍 {job.location}</div>}
                        </div>
                        <div className="flex flex-col gap-3 items-end">
                          <div className="px-4 py-2 rounded-full font-bold text-[0.9rem]" style={{ background: `${scoreColor}20`, color: scoreColor }}>
                            {score.toFixed(0)}% match
                          </div>
                          <div className={`px-4 py-2 rounded-full font-bold text-[0.75rem] text-white ${
                            match.recruiter_status.toLowerCase() === "shortlisted" ? "bg-green-600" :
                            match.recruiter_status.toLowerCase() === "rejected" ? "bg-red-600" :
                            "bg-blue-600"
                          }`}>
                            {match.recruiter_status.charAt(0).toUpperCase() + match.recruiter_status.slice(1)}
                          </div>
                        </div>
                      </div>

                      <div className="mb-6">
                        <div className="flex justify-between mb-2">
                          <span className="text-[0.85rem] font-bold text-[#1d1b19]">Overall Score</span>
                          <span className="text-[0.85rem] font-bold text-[#3525cd]">{score.toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-[#f8f3ee] rounded-full h-2 overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-[#3525cd] to-[#4f46e5]" style={{ width: `${score}%` }} />
                        </div>
                      </div>

                      {(match.matched_skills?.length || match.missing_skills?.length) && (
                        <div className="grid md:grid-cols-2 gap-6 mb-6 pb-6 border-b border-[#f8f3ee]">
                          {match.matched_skills?.length ? (
                            <div>
                              <div className="text-[0.85rem] font-bold text-green-600 mb-3">✓ Matched Skills</div>
                              <div className="flex flex-wrap gap-2">
                                {match.matched_skills.map((s) => (
                                  <span key={s} className="px-3 py-1 rounded-full bg-green-50 text-green-700 text-[0.75rem] font-semibold border border-green-200">
                                    {s}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ) : null}
                          {match.missing_skills?.length ? (
                            <div>
                              <div className="text-[0.85rem] font-bold text-red-600 mb-3">✗ Missing Skills</div>
                              <div className="flex flex-wrap gap-2">
                                {match.missing_skills.map((s, idx) => (
                                  <span key={`${s}-${idx}`} className="px-3 py-1 rounded-full bg-red-50 text-red-700 text-[0.75rem] font-semibold border border-red-200">
                                    {s}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ) : null}
                        </div>
                      )}

                      {match.match_reasoning && (
                        <div className="mb-6 p-4 rounded-lg bg-[#fdf8f3] border border-[#f8f3ee]">
                          <div className="text-[0.85rem] font-bold text-[#3525cd] mb-2">Match Reasoning</div>
                          <p className="text-[#515f74] text-[0.9rem] leading-relaxed">{match.match_reasoning}</p>
                        </div>
                      )}

                      <div className="flex justify-between items-center pt-4">
                        <span className="text-[0.8rem] text-[#515f74]">Matched {new Date(match.created_at).toLocaleDateString()}</span>
                        {job && (
                          <Link href={`/jobs/${job.id}`} className="text-[0.85rem] font-bold text-[#3525cd] hover:text-[#4f46e5]">
                            View Job →
                          </Link>
                        )}
                      </div>
                    </div>
                  );
                })
            )}
          </div>
        )}
      </main>
    </div>
  );
}