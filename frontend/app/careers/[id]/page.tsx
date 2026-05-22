"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";

type Job = {
  id: string;
  title: string;
  description: string;
  requirements: string | null;
  responsibilities: string | null;
  location: string | null;
  employment_type: string | null;
  required_skills: string[];
  salary_min?: number;
  salary_max?: number;
};

export default function PublicJobDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Form State
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [applying, setApplying] = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);

  useEffect(() => {
    if (!params.id) return;
    const fetchJob = async () => {
      try {
        const res = await api.get<Job>(`/api/jobs/public/${params.id}`);
        setJob(res.data);
      } catch (err) {
        setError("Role not found or no longer active.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchJob();
  }, [params.id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !params.id) return;

    setApplying(true);
    const formData = new FormData();
    formData.append("job_id", params.id);
    formData.append("candidate_name", name);
    formData.append("candidate_email", email);
    if (phone) formData.append("candidate_phone", phone);
    formData.append("file", file);

    try {
      await api.postForm("/api/resumes/public/apply", formData);
      setApplySuccess(true);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      console.error(err);
      alert("Failed to submit application. Please try again.");
    } finally {
      setApplying(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#fdf8f3] p-10 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#3525cd]" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen bg-[#fdf8f3] flex flex-col items-center justify-center p-6 text-center">
        <h1 className="text-3xl font-bold text-[#1d1b19] mb-4">Role Not Found</h1>
        <p className="text-[#515f74] mb-8">{error}</p>
        <Link href="/careers" className="px-6 py-3 bg-[#3525cd] text-white rounded-full font-bold">
          Back to Careers
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#fdf8f3] font-sans">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 h-14 flex items-center justify-between px-10 bg-[rgba(253,248,243,0.92)] backdrop-blur-2xl border-b border-[rgba(232,223,214,0.6)]">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[#3525cd]" />
          <span className="text-sm font-extrabold text-[#1d1b19] tracking-tight">AuraRecruiting</span>
        </div>
        <Link href="/careers" className="text-[0.85rem] font-medium text-[#515f74] hover:text-[#1d1b19] transition-colors">
          ← All Positions
        </Link>
      </nav>

      <main className="pt-24 pb-20 px-6 max-w-6xl mx-auto">
        {applySuccess ? (
          <div className="max-w-2xl mx-auto py-20 text-center bg-white rounded-[2rem] border border-[#e8dfd6] shadow-xl p-10">
            <div className="text-6xl mb-6">🎉</div>
            <h1 className="text-3xl font-extrabold text-[#1d1b19] mb-4">Application Submitted!</h1>
            <p className="text-[#515f74] text-lg mb-8 leading-relaxed">
              Thanks for applying to the <span className="font-bold text-[#1d1b19]">{job.title}</span> role.
              Our AI is currently analyzing your resume, and our team will reach out soon.
            </p>
            <Link href="/careers" className="inline-block px-8 py-3 bg-[#3525cd] text-white rounded-full font-bold hover:bg-[#4f46e5] transition-colors">
              View Other Roles
            </Link>
          </div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-12">
            <div className="lg:col-span-2 space-y-10">
              {/* Job Info */}
              <div>
                <div className="text-[0.7rem] font-bold text-[#3525cd] uppercase tracking-widest mb-4">Job Details</div>
                <h1 className="text-[clamp(2rem,4vw,3.5rem)] font-extrabold tracking-[-0.035em] leading-[1.1] text-[#1d1b19] mb-6">
                  {job.title}
                </h1>
                <div className="flex flex-wrap items-center gap-4 text-[#515f74]">
                  <span className="px-4 py-1.5 rounded-full bg-white border border-[#e8dfd6] text-sm font-semibold">📍 {job.location || "Remote"}</span>
                  <span className="px-4 py-1.5 rounded-full bg-white border border-[#e8dfd6] text-sm font-semibold capitalize">💼 {job.employment_type?.replace("-", " ") || "Full-time"}</span>
                  {job.salary_min && (
                    <span className="px-4 py-1.5 rounded-full bg-green-50 text-green-700 border border-green-100 text-sm font-bold">
                      ${job.salary_min.toLocaleString()}+
                    </span>
                  )}
                </div>
              </div>

              <div className="bg-white rounded-3xl border border-[#e8dfd6] p-8 space-y-8">
                <section>
                  <h2 className="text-xl font-bold text-[#1d1b19] mb-4">Description</h2>
                  <div className="text-[#515f74] leading-[1.8] whitespace-pre-wrap">{job.description}</div>
                </section>

                {job.requirements && (
                  <section>
                    <h2 className="text-xl font-bold text-[#1d1b19] mb-4">Requirements</h2>
                    <div className="text-[#515f74] leading-[1.8] whitespace-pre-wrap">{job.requirements}</div>
                  </section>
                )}

                {job.required_skills && job.required_skills.length > 0 && (
                  <section>
                    <h2 className="text-xl font-bold text-[#1d1b19] mb-4">Key Skills</h2>
                    <div className="flex flex-wrap gap-2">
                      {job.required_skills.map((skill) => (
                        <span key={skill} className="px-3 py-1 bg-[#3525cd]/10 text-[#3525cd] rounded-lg text-sm font-semibold">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </section>
                )}
              </div>
            </div>

            {/* Sidebar Form */}
            <div className="lg:sticky lg:top-24 h-fit">
              <div className="bg-white rounded-3xl border border-[#e8dfd6] shadow-xl overflow-hidden">
                <div className="bg-[#1d1b19] p-6 text-white">
                  <h3 className="text-lg font-bold mb-1">Apply for this role</h3>
                  <p className="text-white/60 text-sm">Takes less than 2 minutes.</p>
                </div>
                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                  <div>
                    <label htmlFor="candidate-name" className="text-xs font-bold text-[#1d1b19] uppercase tracking-wider block mb-2">Full Name</label>
                    <input
                      id="candidate-name"
                      required
                      type="text"
                      placeholder="Jane Doe"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full px-4 py-3 bg-[#f8f3ee] border-transparent focus:bg-white focus:ring-2 focus:ring-[#3525cd] rounded-xl text-sm transition-all"
                    />
                  </div>
                  <div>
                    <label htmlFor="candidate-email" className="text-xs font-bold text-[#1d1b19] uppercase tracking-wider block mb-2">Email Address</label>
                    <input
                      id="candidate-email"
                      required
                      type="email"
                      placeholder="jane@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full px-4 py-3 bg-[#f8f3ee] border-transparent focus:bg-white focus:ring-2 focus:ring-[#3525cd] rounded-xl text-sm transition-all"
                    />
                  </div>
                  <div>
                    <label htmlFor="candidate-phone" className="text-xs font-bold text-[#1d1b19] uppercase tracking-wider block mb-2">Phone (Optional)</label>
                    <input
                      id="candidate-phone"
                      type="tel"
                      placeholder="+1 (555) 000-0000"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      className="w-full px-4 py-3 bg-[#f8f3ee] border-transparent focus:bg-white focus:ring-2 focus:ring-[#3525cd] rounded-xl text-sm transition-all"
                    />
                  </div>
                  <div>
                    <label htmlFor="candidate-resume" className="text-xs font-bold text-[#1d1b19] uppercase tracking-wider block mb-2">Resume (PDF)</label>
                    <div className="relative group">
                      <input
                        id="candidate-resume"
                        required
                        type="file"
                        accept=".pdf"
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                      />
                      <div className="w-full px-4 py-8 border-2 border-dashed border-[#e8dfd6] group-hover:border-[#3525cd] bg-[#fdf8f3] rounded-2xl flex flex-col items-center justify-center text-center transition-all">
                        <div className="text-2xl mb-2">📄</div>
                        <p className="text-xs font-bold text-[#1d1b19]">
                          {file ? file.name : "Click to upload PDF"}
                        </p>
                        <p className="text-[10px] text-[#515f74] mt-1">Up to 10MB</p>
                      </div>
                    </div>
                  </div>

                  <button
                    disabled={applying}
                    type="submit"
                    className="w-full py-4 bg-[#3525cd] hover:bg-[#4f46e5] text-white rounded-2xl font-bold shadow-lg shadow-[#3525cd]/20 transition-all transform active:scale-95 disabled:opacity-50"
                  >
                    {applying ? "Submitting..." : "Submit Application"}
                  </button>
                  <p className="text-[10px] text-[#515f74] text-center px-4">
                    By applying, you agree to our Terms of Service and Privacy Policy.
                  </p>
                </form>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
