"use client";

import { useEffect } from "react";
import Link from "next/link";

const ArrowIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <path d="M5 12h14M12 5l7 7-7 7" />
  </svg>
);

const LightningIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
  </svg>
);

const CheckIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10" />
    <path d="m9 12 2 2 4-4" />
  </svg>
);

const KanbanIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="7" height="7" />
    <rect x="14" y="3" width="7" height="7" />
    <rect x="3" y="14" width="7" height="7" />
    <rect x="14" y="14" width="7" height="7" />
  </svg>
);

const TeamIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
  </svg>
);

const SecurityIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="11" width="18" height="11" rx="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

const GreenhouseIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-green-700">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
  </svg>
);

const LeverIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-blue-600">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15h4v-2h-4v2zm0-4h4v-2h-4v2zm0-4h4V7h-4v2z"/>
  </svg>
);

const WorkdayIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-blue-500">
    <path d="M20 3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H4V8h16v11z"/>
  </svg>
);

const SlackIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-purple-600">
    <path d="M5.5 12c0 .825-.675 1.5-1.5 1.5S2.5 12.825 2.5 12 3.175 10.5 4 10.5 5.5 11.175 5.5 12zm7.5 0c0 .825-.675 1.5-1.5 1.5s-1.5-.675-1.5-1.5.675-1.5 1.5-1.5 1.5.675 1.5 1.5zm7.5 0c0 .825-.675 1.5-1.5 1.5s-1.5-.675-1.5-1.5.675-1.5 1.5-1.5 1.5.675 1.5 1.5z"/>
  </svg>
);

const SalesforceIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-orange-600">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-13c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5z"/>
  </svg>
);

const OktaIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-pink-600">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.5-9c.825 0 1.5-.675 1.5-1.5S16.325 8 15.5 8 14 8.675 14 9.5s.675 1.5 1.5 1.5zm-7 0c.825 0 1.5-.675 1.5-1.5S9.325 8 8.5 8 7 8.675 7 9.5 7.675 11 8.5 11zm3.5 4c1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3 1.34 3 3 3z"/>
  </svg>
);

const DocsIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
  </svg>
);

const ChartIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
);

export default function LandingPage() {
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) =>
        entries.forEach((x) => {
          if (x.isIntersecting) x.target.classList.add("v");
        }),
      { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
    );
    document.querySelectorAll(".reveal").forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);

  return (
    <div className="min-h-screen bg-[#fdf8f3] font-sans overflow-x-hidden">
      <style>{`
        .reveal { opacity: 0; transform: translateY(22px); transition: opacity 0.6s ease, transform 0.6s ease; }
        .reveal.v { opacity: 1; transform: none; }
        .d1 { transition-delay: 0.1s; }
        .d2 { transition-delay: 0.2s; }
        .d3 { transition-delay: 0.3s; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .animate-pulse { animation: pulse 2s infinite; }
      `}</style>

      {/* NAV */}
      <nav className="fixed top-0 left-0 right-0 z-50 h-14 flex items-center justify-between px-10 bg-[rgba(253,248,243,0.92)] backdrop-blur-2xl border-b border-[rgba(232,223,214,0.6)]">
        <Link 
          href="/login" 
          className="flex items-center gap-2 hover:opacity-80 transition-opacity"
        >
          <div className="w-2 h-2 rounded-full bg-[#3525cd]" />
          <span className="text-sm font-extrabold text-[#1d1b19] tracking-tight">AuraRecruiting</span>
        </Link>

        <div className="hidden md:flex items-center gap-8 absolute left-1/2 -translate-x-1/2">
          <a href="#features" className="text-[0.85rem] font-medium text-[#515f74] hover:text-[#1d1b19] transition-colors">Platform</a>
        </div>

        <div className="flex items-center gap-4">
          <Link href="/login" className="text-[0.825rem] font-bold text-[#3525cd] px-5 py-2 rounded-full border border-[#3525cd] hover:bg-[rgba(53,37,205,0.05)] transition-all">
            Login
          </Link>
          <Link href="/demo" className="text-[0.825rem] font-bold text-white px-5 py-2 rounded-full bg-[#3525cd] hover:bg-[#4f46e5] transition-colors transform hover:-translate-y-0.5 shadow-lg shadow-[#3525cd]/15">
            Book a Demo
          </Link>
        </div>
      </nav>

      {/* HERO */}
      <section className="pt-32 pb-20 px-6 text-center bg-[#fdf8f3] relative overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,rgba(53,37,205,0.07),transparent_70%)] pointer-events-none" />

        <div className="inline-flex items-center gap-2 border border-[rgba(53,37,205,0.25)] bg-[rgba(53,37,205,0.06)] rounded-full px-4 py-1.5 mb-7">
          <span className="w-1.5 h-1.5 rounded-full bg-[#3525cd] animate-pulse" />
          <span className="text-[0.7rem] font-bold text-[#3525cd] tracking-widest uppercase">AI-Powered Recruiting</span>
        </div>

        <h1 className="text-[clamp(2.6rem,5.5vw,4.8rem)] font-extrabold tracking-[-0.035em] leading-[1.08] text-[#1d1b19] max-w-3xl mx-auto mb-5">
          The Talent Hub:<br />
          <span className="text-[#3525cd]">Hire Anything.</span>
        </h1>

        <p className="text-[clamp(0.95rem,1.2vw,1.1rem)] text-[#515f74] max-w-2xl mx-auto mb-9 leading-[1.75]">
          Bridge the gap between your talent needs and the best candidates. Aura intelligently matches candidates with surgical precision.
        </p>

        <div className="flex items-center justify-center gap-3 flex-wrap mb-16">
          <a href="#features" className="inline-flex items-center gap-2 text-[0.9rem] font-bold text-white px-7 py-3 rounded-[0.625rem] bg-[#1d1b19] hover:bg-[#2d2926] transition-all hover:-translate-y-0.5">
            Explore Features
            <ArrowIcon />
          </a>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto">
          {/* Box 1: Dashboard Tab */}
          <div className="relative group bg-white rounded-2xl overflow-hidden shadow-[0_8px_30px_rgba(0,0,0,0.06)] border border-[#f0e8e0] flex flex-col hover:-translate-y-2 hover:shadow-2xl hover:shadow-[#3525cd]/15 transition-all duration-300">
            <div className="absolute inset-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:14px_14px] opacity-20 group-hover:opacity-60 transition-opacity duration-500" />
            <div className="absolute inset-0 bg-gradient-to-b from-transparent to-white/90 z-0" />
            <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-[#eeefff] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            
            <div className="relative z-10 flex flex-col h-full">
              <div className="h-8 flex items-center px-4 gap-1.5 flex-shrink-0 border-b border-[#f8f3ee]/60 bg-white/50 backdrop-blur-sm">
                <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#27c93f]" />
              </div>
              <div className="p-6 flex-1 flex flex-col items-center text-center gap-4">
                <div className="relative mt-2">
                  <div className="absolute inset-0 bg-[#3525cd] rounded-2xl blur-xl opacity-20 group-hover:opacity-60 transition-opacity duration-300" />
                  <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-[#3525cd] to-[#5a4df7] shadow-xl border border-white/20 flex items-center justify-center text-white transform group-hover:scale-110 group-hover:-rotate-6 transition-all duration-300">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
                      <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
                    </svg>
                  </div>
                </div>
                <div className="mt-2 text-center h-full flex flex-col">
                  <div className="text-[1.1rem] font-extrabold text-[#1d1b19] tracking-tight group-hover:text-[#3525cd] transition-colors">Dashboard</div>
                  <div className="mb-3 mt-2"><span className="text-[0.65rem] font-bold bg-[#f8f3ee] text-[#515f74] px-3 py-1 rounded-full group-hover:bg-[#e0dfff] group-hover:text-[#3525cd] transition-colors tracking-widest uppercase">Analytics</span></div>
                  <p className="text-[0.85rem] text-[#64748b] leading-relaxed mt-auto">Monitor your hiring velocity and track AI match scores in real-time.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Box 2: Jobs Tab */}
          <div className="relative group bg-white rounded-2xl overflow-hidden shadow-[0_8px_30px_rgba(0,0,0,0.06)] border border-[#f0e8e0] flex flex-col hover:-translate-y-2 hover:shadow-2xl hover:shadow-[#10b981]/15 transition-all duration-300">
            <div className="absolute inset-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:14px_14px] opacity-20 group-hover:opacity-60 transition-opacity duration-500" />
            <div className="absolute inset-0 bg-gradient-to-b from-transparent to-white/90 z-0" />
            <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-[#ecfdf5] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            
            <div className="relative z-10 flex flex-col h-full">
              <div className="h-8 flex items-center px-4 gap-1.5 flex-shrink-0 border-b border-[#f8f3ee]/60 bg-white/50 backdrop-blur-sm">
                <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#27c93f]" />
              </div>
              <div className="p-6 flex-1 flex flex-col items-center text-center gap-4">
                <div className="relative mt-2">
                  <div className="absolute inset-0 bg-[#059669] rounded-2xl blur-xl opacity-20 group-hover:opacity-60 transition-opacity duration-300" />
                  <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-[#10b981] to-[#047857] shadow-xl border border-white/20 flex items-center justify-center text-white transform group-hover:scale-110 group-hover:rotate-6 transition-all duration-300">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
                    </svg>
                  </div>
                </div>
                <div className="mt-2 text-center h-full flex flex-col">
                  <div className="text-[1.1rem] font-extrabold text-[#1d1b19] tracking-tight group-hover:text-[#059669] transition-colors">Jobs</div>
                  <div className="mb-3 mt-2"><span className="text-[0.65rem] font-bold bg-[#f8f3ee] text-[#515f74] px-3 py-1 rounded-full group-hover:bg-[#d1fae5] group-hover:text-[#047857] transition-colors tracking-widest uppercase">Pipeline</span></div>
                  <p className="text-[0.85rem] text-[#64748b] leading-relaxed mt-auto">Manage active roles using our intuitive Kanban stage tracking.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Box 3: Candidates Tab */}
          <div className="relative group bg-white rounded-2xl overflow-hidden shadow-[0_8px_30px_rgba(0,0,0,0.06)] border border-[#f0e8e0] flex flex-col hover:-translate-y-2 hover:shadow-2xl hover:shadow-[#f59e0b]/15 transition-all duration-300">
            <div className="absolute inset-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:14px_14px] opacity-20 group-hover:opacity-60 transition-opacity duration-500" />
            <div className="absolute inset-0 bg-gradient-to-b from-transparent to-white/90 z-0" />
            <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-[#fffbeb] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            
            <div className="relative z-10 flex flex-col h-full">
              <div className="h-8 flex items-center px-4 gap-1.5 flex-shrink-0 border-b border-[#f8f3ee]/60 bg-white/50 backdrop-blur-sm">
                <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#27c93f]" />
              </div>
              <div className="p-6 flex-1 flex flex-col items-center text-center gap-4">
                <div className="relative mt-2">
                  <div className="absolute inset-0 bg-[#d97706] rounded-2xl blur-xl opacity-20 group-hover:opacity-60 transition-opacity duration-300" />
                  <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-[#f59e0b] to-[#b45309] shadow-xl border border-white/20 flex items-center justify-center text-white transform group-hover:scale-110 group-hover:-rotate-6 transition-all duration-300">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
                      <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                    </svg>
                  </div>
                </div>
                <div className="mt-2 text-center h-full flex flex-col">
                  <div className="text-[1.1rem] font-extrabold text-[#1d1b19] tracking-tight group-hover:text-[#d97706] transition-colors">Candidates</div>
                  <div className="mb-3 mt-2"><span className="text-[0.65rem] font-bold bg-[#f8f3ee] text-[#515f74] px-3 py-1 rounded-full group-hover:bg-[#fef3c7] group-hover:text-[#b45309] transition-colors tracking-widest uppercase">Auto Mapped</span></div>
                  <p className="text-[0.85rem] text-[#64748b] leading-relaxed mt-auto">Automatically parse resumes and rank top talent instantly.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Box 4: LinkedIn Tab */}
          <div className="relative group bg-white rounded-2xl overflow-hidden shadow-[0_8px_30px_rgba(0,0,0,0.06)] border border-[#f0e8e0] flex flex-col hover:-translate-y-2 hover:shadow-2xl hover:shadow-[#0a66c2]/15 transition-all duration-300">
            <div className="absolute inset-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:14px_14px] opacity-20 group-hover:opacity-60 transition-opacity duration-500" />
            <div className="absolute inset-0 bg-gradient-to-b from-transparent to-white/90 z-0" />
            <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-[#eff6ff] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            
            <div className="relative z-10 flex flex-col h-full">
              <div className="h-8 flex items-center px-4 gap-1.5 flex-shrink-0 border-b border-[#f8f3ee]/60 bg-white/50 backdrop-blur-sm">
                <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#27c93f]" />
              </div>
              <div className="p-6 flex-1 flex flex-col items-center text-center gap-4">
                <div className="relative mt-2">
                  <div className="absolute inset-0 bg-[#0a66c2] rounded-2xl blur-xl opacity-20 group-hover:opacity-60 transition-opacity duration-300" />
                  <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-[#0a66c2] to-[#0855a1] shadow-xl border border-white/20 flex items-center justify-center text-white transform group-hover:scale-110 group-hover:rotate-6 transition-all duration-300">
                     <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                    </svg>
                  </div>
                </div>
                <div className="mt-2 text-center h-full flex flex-col">
                  <div className="text-[1.1rem] font-extrabold text-[#1d1b19] tracking-tight group-hover:text-[#0a66c2] transition-colors">LinkedIn</div>
                  <div className="mb-3 mt-2"><span className="text-[0.65rem] font-bold bg-[#f8f3ee] text-[#515f74] px-3 py-1 rounded-full group-hover:bg-[#dbeafe] group-hover:text-[#0a66c2] transition-colors tracking-widest uppercase">Generative AI</span></div>
                  <p className="text-[0.85rem] text-[#64748b] leading-relaxed mt-auto">Craft viral job posts tailored for social networks in one click.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>


      {/* SPLIT: AI SCORING */}
      <section className="py-24 px-6 bg-[#fdf8f3]" id="features">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-16 items-center">
          <div className="reveal">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-6 h-0.5 bg-[#3525cd]" />
              <span className="text-[0.68rem] font-bold text-[#3525cd] tracking-widest uppercase">The Intelligence Engine</span>
            </div>
            <h2 className="text-[clamp(1.6rem,2.5vw,2.4rem)] font-extrabold tracking-tight text-[#1d1b19] leading-[1.15] mb-4">Intelligent Candidate Matching</h2>
            <p className="text-[0.925rem] text-[#515f74] leading-[1.75] mb-8">
              Aura's AI reads every resume and matches candidates against your job description with precision. Get instant candidate rankings as resumes arrive in your pipeline.
            </p>
            <div className="flex flex-col gap-4">
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-[rgba(53,37,205,0.08)] flex items-center justify-center flex-shrink-0">
                  <LightningIcon />
                </div>
                <div>
                  <h4 className="font-bold text-[#1d1b19] mb-1">Instant Candidate Scoring</h4>
                  <p className="text-[0.825rem] text-[#515f74] leading-[1.6]">Candidates are evaluated the moment a resume arrives. See ranked results immediately in your pipeline.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-[rgba(239,68,68,0.08)] flex items-center justify-center flex-shrink-0 text-red-600">
                  <CheckIcon />
                </div>
                <div>
                  <h4 className="font-bold text-[#1d1b19] mb-1">Context-Aware Skill Extraction</h4>
                  <p className="text-[0.825rem] text-[#515f74] leading-[1.6]">Our AI reads beyond exact keywords. It understands context, extracting actual experience and matching it to your job requirements perfectly.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="reveal d1">
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div className="bg-white rounded-[0.875rem] p-5 border border-[#f8f3ee] shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
                <div className="text-[1.8rem] font-extrabold tracking-tight text-[#1d1b19] leading-none">AI-Powered</div>
                <div className="text-[0.75rem] text-[#515f74] mt-1">Candidate Matching</div>
              </div>
              <div className="bg-white rounded-[0.875rem] p-5 border border-[#f8f3ee] shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
                <div className="text-[1.8rem] font-extrabold tracking-tight text-[#1d1b19] leading-none">Real-time</div>
                <div className="text-[0.75rem] text-[#515f74] mt-1">Rankings</div>
              </div>
            </div>

            <div className="bg-[#1a1730] rounded-[0.875rem] p-5 border border-[rgba(255,255,255,0.05)] shadow-[0_8px_40px_rgba(0,0,0,0.18)]">
              <div className="h-8 bg-[#13112a] rounded-[0.5rem] mb-4 flex items-center gap-2 px-3 border-b border-[rgba(255,255,255,0.04)]">
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <div className="w-2 h-2 rounded-full bg-yellow-400" />
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-[0.7rem] text-[rgba(255,255,255,0.3)] ml-2">SYNC_ENGINE_v3.1.09</span>
              </div>
              <div className="font-mono text-[0.75rem] space-y-1 text-[rgba(255,255,255,0.55)]">
                <div><span className="text-[#7c6fff] font-bold">SYNC</span> Resume received from upload pipeline</div>
                <div><span className="text-[#4ade80] font-bold">PARSE</span> Extracting skills, experience, education</div>
                <div><span className="text-[#fbbf24] font-bold">MATCH</span> Comparing against JD vectors... done</div>
                <div><span className="text-[#34d399] font-bold">SCORE</span> candidate_score: 94 → ranked #1</div>
                <div><span className="text-[rgba(255,255,255,0.25)] font-bold">INFO</span> <span className="text-[rgba(255,255,255,0.25)]">Pipeline updated in Kanban board</span></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SPLIT: CANDIDATE PIPELINE */}
      <section className="py-24 px-6 bg-white">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-16 items-center">
          <div className="reveal md:order-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-6 h-0.5 bg-[#3525cd]" />
              <span className="text-[0.68rem] font-bold text-[#3525cd] tracking-widest uppercase">Candidate Pipeline</span>
            </div>
            <h2 className="text-[clamp(1.6rem,2.5vw,2.4rem)] font-extrabold tracking-tight text-[#1d1b19] leading-[1.15] mb-4">Your entire pipeline, beautifully organised</h2>
            <p className="text-[0.925rem] text-[#515f74] leading-[1.75] mb-8">
              From first application to final offer — one kanban board for your whole team. Add notes, assign stages, send feedback, and never lose track of a candidate.
            </p>
            <div className="flex flex-col gap-4">
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-[rgba(16,185,129,0.08)] flex items-center justify-center flex-shrink-0 text-green-600">
                  <KanbanIcon />
                </div>
                <div>
                  <h4 className="font-bold text-[#1d1b19] mb-1">Drag-and-Drop Kanban</h4>
                  <p className="text-[0.825rem] text-[#515f74] leading-[1.6]">Move candidates across stages with a single drag. Stages auto-update for all team members in real time.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-[rgba(245,158,11,0.08)] flex items-center justify-center flex-shrink-0 text-amber-600">
                  <TeamIcon />
                </div>
                <div>
                  <h4 className="font-bold text-[#1d1b19] mb-1">Team Collaboration</h4>
                  <p className="text-[0.825rem] text-[#515f74] leading-[1.6]">Leave scorecards, mentions, and feedback notes directly on candidate profiles. Everyone stays aligned.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="reveal d1 md:order-1">
            {/* The Outer App Window */}
            <div className="bg-[#fdfaf7] rounded-[1.25rem] border border-[#eae0d5] shadow-[0_24px_80px_-12px_rgba(53,37,205,0.15)] overflow-hidden flex flex-col h-[400px] relative group transition-all duration-500 hover:shadow-[0_32px_100px_-12px_rgba(53,37,205,0.25)]">
              
              {/* Workspace Blueprint Grid */}
              <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:16px_16px] pointer-events-none" />

              {/* Top Navigation Bar */}
              <div className="px-5 py-4 border-b border-[#eae0d5] bg-white/90 backdrop-blur-xl flex items-center justify-between z-20 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#10b981] to-[#047857] shadow-inner flex items-center justify-center">
                    <span className="text-white text-[10px] font-extrabold tracking-wider">DA</span>
                  </div>
                  <div>
                    <h3 className="text-[0.9rem] font-extrabold text-[#1d1b19] leading-tight">Data Analyst Pipeline</h3>
                    <p className="text-[0.65rem] text-[#64748b] font-medium">4 Active Candidates</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="hidden sm:flex -space-x-2">
                    <div className="w-7 h-7 rounded-full border-2 border-white bg-gradient-to-tr from-[#3525cd] to-[#6d64eb] text-white text-[9px] font-bold flex items-center justify-center shadow-sm">JS</div>
                    <div className="w-7 h-7 rounded-full border-2 border-white bg-gradient-to-tr from-[#f59e0b] to-[#fbbf24] text-white text-[9px] font-bold flex items-center justify-center shadow-sm">MK</div>
                  </div>
                  <div className="px-3 py-1.5 rounded-md bg-[#3525cd] text-white text-[0.7rem] font-bold shadow shadow-[#3525cd]/30 cursor-pointer hover:bg-[#2c1eb3] transition-colors">
                    + Invite
                  </div>
                </div>
              </div>
              
              {/* Kanban Columns Area */}
              <div className="p-5 flex gap-4 overflow-hidden h-full z-10 relative">
                
                {/* Column 1: New */}
                <div className="flex-1 min-w-[150px] flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-[#3b82f6] shadow-[0_0_8px_#3b82f6]" />
                      <span className="text-[0.7rem] font-bold text-[#1d1b19] uppercase tracking-widest">New Stage</span>
                    </div>
                    <span className="text-[0.65rem] font-bold bg-[#eff6ff] text-[#3b82f6] px-2 py-0.5 rounded-full border border-[#bfdbfe]">2</span>
                  </div>

                  {/* Card 1 */}
                  <div className="bg-white p-3.5 rounded-xl border border-[#eae0d5] shadow-sm flex flex-col gap-3 group/card hover:border-[#3525cd]/40 hover:shadow-md transition-all cursor-grab relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-bl from-[#eeefff] to-transparent rounded-bl-full opacity-50 pointer-events-none" />
                    <div className="flex justify-between items-start relative z-10">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#818cf8] to-[#4f46e5] text-white text-[10px] font-bold flex items-center justify-center shadow-inner">P</div>
                        <div className="text-[0.8rem] font-extrabold text-[#1d1b19]">Priya S.</div>
                      </div>
                      <div className="text-[0.65rem] font-bold text-[#3525cd] bg-white px-2 py-0.5 rounded-md shadow-sm border border-[#3525cd]/20 backdrop-blur-sm">94% Fit</div>
                    </div>
                    <div className="text-[0.65rem] text-[#64748b] font-medium leading-tight relative z-10">4 yrs exp · Sr. Analyst</div>
                    <div className="flex gap-1.5 relative z-10">
                       <span className="text-[0.55rem] font-bold bg-[#f1f5f9] text-[#475569] px-2 py-0.5 rounded uppercase tracking-wider">SQL</span>
                       <span className="text-[0.55rem] font-bold bg-[#f1f5f9] text-[#475569] px-2 py-0.5 rounded uppercase tracking-wider">Tableau</span>
                    </div>
                  </div>

                  {/* Card 2 */}
                  <div className="bg-white p-3.5 rounded-xl border border-[#eae0d5] shadow-sm flex flex-col gap-3 group/card hover:border-[#3525cd]/40 hover:shadow-md transition-all cursor-grab overflow-hidden">
                    <div className="flex justify-between items-start">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#fbbf24] to-[#f59e0b] text-white text-[10px] font-bold flex items-center justify-center shadow-inner">A</div>
                        <div className="text-[0.8rem] font-extrabold text-[#1d1b19]">Arjun M.</div>
                      </div>
                      <div className="text-[0.65rem] font-bold text-[#d97706] bg-[#fffbeb] px-2 py-0.5 rounded-md border border-[#fcd34d]">87% Fit</div>
                    </div>
                    <div className="text-[0.65rem] text-[#64748b] font-medium leading-tight">3 yrs exp · Data Analyst</div>
                  </div>
                </div>

                {/* Column 2: Reviewing */}
                <div className="flex-1 min-w-[150px] flex flex-col gap-3 relative">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-[#f59e0b] shadow-[0_0_8px_#f59e0b]" />
                      <span className="text-[0.7rem] font-bold text-[#1d1b19] uppercase tracking-widest">Reviewing</span>
                    </div>
                    <span className="text-[0.65rem] font-bold bg-[#fffbeb] text-[#d97706] px-2 py-0.5 rounded-full border border-[#fcd34d]">1</span>
                  </div>

                  {/* Dragged Card - Pop Out Effect */}
                  <div className="bg-white p-3.5 rounded-xl border flex flex-col gap-3 cursor-grabbing z-30 transform hover:scale-[1.02] transition-transform duration-300 shadow-[0_20px_40px_-10px_rgba(53,37,205,0.3)] border-[#3525cd]/50 rotate-2 scale-105 relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-[#eeefff]/50 to-transparent pointer-events-none" />
                    <div className="flex justify-between items-start relative z-10">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#34d399] to-[#10b981] text-white text-[10px] font-bold flex items-center justify-center shadow-inner">K</div>
                        <div className="text-[0.8rem] font-extrabold text-[#1d1b19]">Kavya R.</div>
                      </div>
                      <div className="text-[0.65rem] font-bold text-[#059669] bg-[#ecfdf5] px-2 py-0.5 rounded-md border border-[#a7f3d0]">81% Fit</div>
                    </div>
                    <div className="text-[0.65rem] text-[#64748b] font-medium leading-tight relative z-10">5 yrs exp · BI Analyst</div>
                     <div className="flex gap-1.5 relative z-10">
                       <span className="text-[0.55rem] font-bold bg-[#f1f5f9] text-[#475569] px-2 py-0.5 rounded uppercase tracking-wider">Python</span>
                       <span className="text-[0.55rem] font-bold bg-[#f1f5f9] text-[#475569] px-2 py-0.5 rounded uppercase tracking-wider">Looker</span>
                    </div>
                  </div>
                </div>

                {/* Column 3: Shortlisted */}
                <div className="flex-1 min-w-[150px] flex flex-col gap-3 relative">
                  <div className="absolute inset-y-0 right-0 w-12 bg-gradient-to-l from-[#fdfaf7] to-transparent z-20 pointer-events-none" />
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-[#10b981] shadow-[0_0_8px_#10b981]" />
                      <span className="text-[0.7rem] font-bold text-[#1d1b19] uppercase tracking-widest">Shortlist</span>
                    </div>
                    <span className="text-[0.65rem] font-bold bg-[#ecfdf5] text-[#059669] px-2 py-0.5 rounded-full border border-[#a7f3d0]">0</span>
                  </div>

                  {/* Drop Zone */}
                  <div className="border-2 border-dashed border-[#818cf8] bg-[#eeefff]/50 rounded-xl h-[100px] flex items-center justify-center relative overflow-hidden group/drop transition-colors duration-300">
                    <div className="absolute inset-0 bg-gradient-to-br from-[#3525cd]/5 to-[#3525cd]/0 animate-pulse pointer-events-none" />
                    <div className="flex flex-col items-center gap-1">
                      <div className="w-6 h-6 rounded-full bg-white shadow-sm flex items-center justify-center text-[#3525cd] transform group-hover/drop:-translate-y-1 transition-transform">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      </div>
                      <span className="text-[0.6rem] text-[#3525cd] font-bold text-center uppercase tracking-wider">Drop to Shortlist</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SPLIT: LINKEDIN AI */}
      <section className="py-24 px-6 bg-[#fdf8f3]">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-16 items-center">
          <div className="reveal">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-6 h-0.5 bg-[#3525cd]" />
              <span className="text-[0.68rem] font-bold text-[#3525cd] tracking-widest uppercase">Social Recruitment</span>
            </div>
            <h2 className="text-[clamp(1.6rem,2.5vw,2.4rem)] font-extrabold tracking-tight text-[#1d1b19] leading-[1.15] mb-4">LinkedIn Post Generator</h2>
            <p className="text-[0.925rem] text-[#515f74] leading-[1.75] mb-8">
              Write the perfect job announcement in seconds. Our AI analyzes your job description and generates viral-ready LinkedIn posts that attract the right quality talent.
            </p>
            <div className="flex flex-col gap-4">
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-[rgba(53,37,205,0.08)] flex items-center justify-center flex-shrink-0">
                  <LightningIcon />
                </div>
                <div>
                  <h4 className="font-bold text-[#1d1b19] mb-1">AI-Powered Copywriting</h4>
                  <p className="text-[0.825rem] text-[#515f74] leading-[1.6]">No more writer's block. Get 3 different versions (Professional, Casual, or Creative) for every job details.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-[rgba(53,37,205,0.08)] flex items-center justify-center flex-shrink-0">
                   <ArrowIcon />
                </div>
                <div>
                  <h4 className="font-bold text-[#1d1b19] mb-1">Smart Hashtags</h4>
                  <p className="text-[0.825rem] text-[#515f74] leading-[1.6]">Automatically includes trending industry hashtags to maximize your reach and visibility.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="reveal d1">
            <div className="bg-white rounded-[1.25rem] border border-[#e8dfd6] shadow-xl p-6">
              <div className="flex items-center gap-3 mb-4 border-b border-[#f8f3ee] pb-4">
                 <div className="w-10 h-10 rounded-full bg-[#0077b5] flex items-center justify-center text-white text-lg">in</div>
                 <div>
                   <div className="text-sm font-bold text-[#1d1b19]">LinkedIn Assistant</div>
                   <div className="text-[0.7rem] text-[#515f74]">Drafting for "Sr. Frontend Engineer"</div>
                 </div>
              </div>
              <div className="bg-[#f0f7ff] rounded-xl p-4 text-[0.8rem] text-[#1d1b19] leading-relaxed mb-4 italic">
                "🚀 We're hiring a Senior Frontend Engineer at Aura! Join us in building the future of recruiting with AI. If you love React and modern tech, let's talk! #Hiring #Frontend #AuraRecruiting"
              </div>
              <div className="flex gap-2">
                <button className="flex-1 py-2 text-[0.7rem] font-bold bg-[#3525cd] text-white rounded-lg">Copy to Clipboard</button>
                <button className="px-4 py-2 text-[0.7rem] font-bold border border-[#e8dfd6] rounded-lg">Regenerate</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SPLIT: PUBLIC CAREERS */}
      <section className="py-24 px-6 bg-white">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-16 items-center">
          <div className="reveal md:order-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-6 h-0.5 bg-[#3525cd]" />
              <span className="text-[0.68rem] font-bold text-[#3525cd] tracking-widest uppercase">Candidate Experience</span>
            </div>
            <h2 className="text-[clamp(1.6rem,2.5vw,2.4rem)] font-extrabold tracking-tight text-[#1d1b19] leading-[1.15] mb-4">Integrated Public Careers Site</h2>
            <p className="text-[0.925rem] text-[#515f74] leading-[1.75] mb-8">
              A high-converting job board that works out of the box. Host your jobs on a branded portal where candidates can apply in under 60 seconds accurately.
            </p>
            <div className="flex flex-col gap-4">
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-[rgba(16,185,129,0.08)] flex items-center justify-center flex-shrink-0 text-green-600">
                  <CheckIcon />
                </div>
                <div>
                  <h4 className="font-bold text-[#1d1b19] mb-1">Direct Resume Upload</h4>
                  <p className="text-[0.825rem] text-[#515f74] leading-[1.6]">Candidates upload PDFs which are instantly parsed and matched. No long forms required.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-[rgba(16,185,129,0.08)] flex items-center justify-center flex-shrink-0 text-green-600">
                   <TeamIcon />
                </div>
                <div>
                  <h4 className="font-bold text-[#1d1b19] mb-1">Real-time Job Updates</h4>
                  <p className="text-[0.825rem] text-[#515f74] leading-[1.6]">When you move a job to "Active" in your dashboard, it appears on your careers site instantly.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="reveal d1 md:order-1">
             <div className="bg-[#fdf8f3] rounded-[1.5rem] border border-[#e8dfd6] shadow-lg overflow-hidden">
                <div className="p-6 border-b border-[#e8dfd6] bg-white">
                   <div className="text-[0.85rem] font-bold text-[#1d1b19]">Careers at AuraRecruiting</div>
                </div>
                <div className="p-6 space-y-4">
                   {[
                     { title: "Senior Product Designer", loc: "Remote", type: "Full-time" },
                     { title: "Backend Engineer (FastAPI)", loc: "San Francisco", type: "Full-time" }
                   ].map((job, i) => (
                     <div key={i} className="p-4 bg-white rounded-xl border border-[#e8dfd6] flex items-center justify-between group cursor-pointer hover:border-[#3525cd] transition-all">
                        <div>
                          <div className="text-sm font-bold text-[#1d1b19]">{job.title}</div>
                          <div className="text-[0.7rem] text-[#515f74]">{job.loc} · {job.type}</div>
                        </div>
                        <div className="w-7 h-7 rounded-full bg-[#fdf8f3] group-hover:bg-[#3525cd] group-hover:text-white flex items-center justify-center transition-all">
                           <ArrowIcon />
                        </div>
                     </div>
                   ))}
                </div>
             </div>
          </div>
        </div>
      </section>



      {/* CTA BANNER */}
      <section className="px-6 py-20 bg-[#fdf8f3]">
        <div className="max-w-5xl mx-auto">
          <div className="reveal bg-[#4f46e5] rounded-[2rem] p-16 text-center relative overflow-hidden shadow-2xl">
            {/* Background Circles to match screenshot */}
            <div className="absolute -left-20 -bottom-20 w-[400px] h-[400px] rounded-full bg-white/10 pointer-events-none" />
            <div className="absolute -right-20 -top-20 w-[300px] h-[300px] rounded-full bg-white/10 pointer-events-none" />
            
            <div className="relative z-10">
              <h2 className="text-[clamp(2rem,4vw,3.2rem)] font-extrabold text-white tracking-tight mb-4">
                Ready to transform your hiring?
              </h2>
              <p className="text-white/80 mb-10 text-[1.1rem] max-w-2xl mx-auto">
                Join 500+ teams already hiring faster and smarter with Aura. Free to start.
              </p>
              <div className="flex items-center justify-center gap-4 flex-wrap">
                <Link href="/signup" className="inline-flex items-center justify-center text-[0.95rem] font-bold text-[#4f46e5] h-14 px-8 rounded-xl bg-white hover:bg-[#eeefff] transition-all hover:-translate-y-1 shadow-lg shadow-black/10">
                  Get Started Free
                </Link>
                <Link href="/demo" className="inline-flex items-center justify-center text-[0.95rem] font-bold text-white h-14 px-8 rounded-xl border-2 border-white/30 bg-white/5 hover:bg-white/15 transition-all hover:-translate-y-1">
                  Talk to our Team Member
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-[#fdf8f3] border-t border-[#f8f3ee] px-6 py-16">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-8 pb-12 mb-8 border-b border-[#f8f3ee]">
            <div className="md:col-span-2">
              <Link 
                href="/login" 
                className="flex items-center gap-2 mb-3 hover:opacity-80 transition-opacity inline-flex"
              >
                <div className="w-2 h-2 rounded-full bg-[#3525cd]" />
                <span className="font-extrabold text-[#1d1b19]">AuraRecruiting</span>
              </Link>
              <p className="text-[0.825rem] text-[#1d1b19] leading-[1.7] max-w-xs mb-4">
                Building the next generation of recruitment intelligence through AI-powered candidate connections.
              </p>

            </div>

            {[
              { title: "Product", links: [{ name: "Platform", url: "#features" }] },
              { title: "Security", links: [{ name: "Trust Center", url: "/trust" }, { name: "SOC Reports", url: "/soc" }, { name: "GDPR", url: "/gdpr" }] },
              { title: "Legal", links: [{ name: "Privacy", url: "/privacy" }, { name: "Terms", url: "/terms" }, { name: "Cookie Policy", url: "/cookies" }] },
            ].map((col) => (
              <div key={col.title}>
                <h4 className="text-[0.72rem] font-bold text-[#1d1b19] uppercase tracking-widest mb-4">{col.title}</h4>
                <div className="space-y-2">
                  {col.links.map((link) => {
                    const isExternal = link.url.startsWith('http');
                    const Component = isExternal ? 'a' : Link;
                    const props = isExternal ? { href: link.url, target: '_blank', rel: 'noopener noreferrer' } : { href: link.url };
                    return (
                      <Component key={link.name} {...props} className="block text-[0.825rem] text-[#1d1b19] hover:text-[#3525cd] transition-colors">
                        {link.name}
                      </Component>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between">
            <span className="text-[0.75rem] text-[#1d1b19]">© 2026 AuraRecruiting. All rights reserved.</span>
            <div className="flex items-center gap-1.5 text-[0.75rem] text-[#1d1b19]">
              <div className="w-1.5 h-1.5 rounded-full bg-[#10b981]" />
              System Status: All Operational
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}