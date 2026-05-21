"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Mail, MapPin, Linkedin, Sparkles, Target, Zap } from "lucide-react";

const ArrowIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <path d="M5 12h14M12 5l7 7-7 7" />
  </svg>
);

export default function DemoPage() {
  const [submitted, setSubmitted] = useState(false);

  return (
    <div className="min-h-screen bg-[#fdf8f3] font-['Plus_Jakarta_Sans',sans-serif] selection:bg-[#3525cd] selection:text-white flex flex-col relative overflow-hidden">
      {/* Background decoration - subtle gradient to match landing page hero */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,rgba(53,37,205,0.05),transparent_70%)] pointer-events-none" />
      
      <header className="px-6 py-8 max-w-7xl mx-auto w-full flex items-center justify-between relative z-20">
        <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <div className="w-4 h-4 bg-[#3525cd] rounded-sm transform rotate-45" />
          <span className="font-extrabold text-[#1d1b19] tracking-tight text-lg">AuraRecruiting</span>
        </Link>
        <Link href="/" className="text-sm font-bold text-[#515f74] hover:text-[#3525cd] flex items-center gap-2 transition-colors">
          <ArrowLeft size={16} />
          Back to Platform
        </Link>
      </header>

      <main className="flex-1 w-full max-w-7xl mx-auto px-6 py-6 lg:py-12 flex items-center relative z-10">
        {submitted ? (
          <div className="bg-white rounded-[2.5rem] p-16 text-center max-w-2xl mx-auto border border-[#f0e8e0] shadow-2xl animate-in fade-in zoom-in duration-500">
             <div className="w-24 h-24 bg-[#eeefff] text-[#3525cd] rounded-full flex items-center justify-center mx-auto mb-8 shadow-lg shadow-[#3525cd]/10">
                <Zap size={40} fill="currentColor" />
             </div>
             <h2 className="text-4xl font-extrabold text-[#1d1b19] mb-4 tracking-tight">You're on the list!</h2>
             <p className="text-xl text-[#515f74] mb-12 leading-relaxed">
               An AuraRecruiting specialist will connect with you within 24 business hours to help you build your perfect hiring pipeline.
             </p>
             <Link href="/" className="inline-flex items-center justify-center h-14 px-10 rounded-2xl bg-[#3525cd] text-white font-bold text-lg hover:bg-[#2c1eb3] transition-all shadow-xl shadow-[#3525cd]/15">
                Return to Landing Page
             </Link>
          </div>
        ) : (
          <div className="w-full grid lg:grid-cols-2 gap-16 xl:gap-24 items-center">
            
            {/* Left Side: Contact Info (Light/Premium) */}
            <div className="animate-in fade-in slide-in-from-left-8 duration-700 ease-out">
               <div className="inline-flex items-center gap-2 border border-[rgba(53,37,205,0.2)] bg-[rgba(53,37,205,0.05)] rounded-full px-4 py-1.5 mb-8">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#3525cd] animate-pulse" />
                  <span className="text-[0.65rem] font-bold text-[#3525cd] tracking-widest uppercase">Expert Strategy Call</span>
               </div>

               <h2 className="text-[clamp(2.5rem,5vw,4rem)] font-extrabold text-[#1d1b19] tracking-tight leading-[1.05] mb-8">
                 Let's build your <br/>
                 <span className="text-[#3525cd]">perfect team.</span>
               </h2>
               <p className="text-[#515f74] text-lg md:text-xl leading-relaxed mb-16 max-w-lg">
                 Talk to our hiring experts to see how Aura intelligently matches candidates with surgical precision.
               </p>

               <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 mb-12">
                 <div className="flex flex-col gap-4 p-6 bg-white rounded-2xl border border-[#f0e8e0] shadow-sm hover:shadow-md transition-shadow">
                    <div className="w-10 h-10 rounded-lg bg-[#eeefff] text-[#3525cd] flex items-center justify-center">
                       <Target size={20} />
                    </div>
                    <div>
                       <h4 className="font-bold text-[#1d1b19] mb-1">Precision Hiring</h4>
                       <p className="text-sm text-[#515f74]">Match talent with 99% accuracy using our AI engine.</p>
                    </div>
                 </div>
                 <div className="flex flex-col gap-4 p-6 bg-white rounded-2xl border border-[#f0e8e0] shadow-sm hover:shadow-md transition-shadow">
                    <div className="w-10 h-10 rounded-lg bg-[#eeefff] text-[#3525cd] flex items-center justify-center">
                       <Sparkles size={20} />
                    </div>
                    <div>
                       <h4 className="font-bold text-[#1d1b19] mb-1">Smart Sourcing</h4>
                       <p className="text-sm text-[#515f74]">Automate your outreach and build viral job posts.</p>
                    </div>
                 </div>
               </div>

               <div className="space-y-6 pt-8 border-t border-[#f0e8e0]">
                 <div className="flex items-center gap-4 text-[#515f74] hover:text-[#3525cd] transition-colors cursor-pointer group">
                   <Mail size={18} className="group-hover:scale-110 transition-transform" />
                   <span className="font-bold tracking-tight">team@aurarecruiting.com</span>
                 </div>
                 <div className="flex items-center gap-4 text-[#515f74]">
                   <MapPin size={18} />
                   <span className="font-medium">HITEC City, Hyderabad, India</span>
                 </div>
                 <div className="flex items-center gap-4 pt-2">
                    <a href="#" className="w-9 h-9 rounded-lg bg-[#3525cd] text-white flex items-center justify-center hover:bg-[#1d1b19] transition-all shadow-lg shadow-[#3525cd]/20">
                      <Linkedin size={16} fill="currentColor" />
                    </a>
                 </div>
               </div>
            </div>

            {/* Right Side: Contact Form (Elevated Card) */}
            <div className="animate-in fade-in slide-in-from-right-8 duration-700 ease-out fill-mode-both">
               <div className="bg-white rounded-[2.5rem] p-8 md:p-12 shadow-[0_32px_80px_-16px_rgba(53,37,205,0.12)] border border-[#f0e8e0]">
                 <div className="mb-10 text-center">
                    <h3 className="text-2xl font-extrabold text-[#1d1b19] mb-2">Request a Walkthrough</h3>
                    <p className="text-sm text-[#515f74]">Briefly tell us about your team's goals.</p>
                 </div>
                 
                 <form 
                   onSubmit={(e) => {
                     e.preventDefault();
                     setSubmitted(true);
                   }} 
                   className="space-y-6"
                 >
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="text-[0.7rem] font-bold text-[#1d1b19] uppercase tracking-wider ml-1">Full Name</label>
                        <input required type="text" placeholder="John Doe" className="w-full bg-[#fdfaf7] border border-[#f0e8e0] focus:border-[#3525cd] focus:ring-1 focus:ring-[#3525cd] rounded-xl px-5 py-4 text-sm transition-all outline-none" />
                      </div>
                      <div className="space-y-2">
                        <label className="text-[0.7rem] font-bold text-[#1d1b19] uppercase tracking-wider ml-1">Work Email</label>
                        <input required type="email" placeholder="john@company.com" className="w-full bg-[#fdfaf7] border border-[#f0e8e0] focus:border-[#3525cd] focus:ring-1 focus:ring-[#3525cd] rounded-xl px-5 py-4 text-sm transition-all outline-none" />
                      </div>
                   </div>

                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="text-[0.7rem] font-bold text-[#1d1b19] uppercase tracking-wider ml-1">Company Size</label>
                        <select className="w-full bg-[#fdfaf7] border border-[#f0e8e0] focus:border-[#3525cd] focus:ring-1 focus:ring-[#3525cd] rounded-xl px-5 py-4 text-sm outline-none appearance-none cursor-pointer">
                          <option>1-50 employees</option>
                          <option>51-200 employees</option>
                          <option>201-500 employees</option>
                          <option>500+ employees</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-[0.7rem] font-bold text-[#1d1b19] uppercase tracking-wider ml-1">Role</label>
                        <input type="text" placeholder="Hiring Manager" className="w-full bg-[#fdfaf7] border border-[#f0e8e0] focus:border-[#3525cd] focus:ring-1 focus:ring-[#3525cd] rounded-xl px-5 py-4 text-sm transition-all outline-none" />
                      </div>
                   </div>

                   <div className="space-y-2">
                     <label className="text-[0.7rem] font-bold text-[#1d1b19] uppercase tracking-wider ml-1">How can we help you?</label>
                     <textarea required rows={4} placeholder="I'm interested in AI matching for our engineering roles..." className="w-full bg-[#fdfaf7] border border-[#f0e8e0] focus:border-[#3525cd] focus:ring-1 focus:ring-[#3525cd] rounded-xl px-5 py-4 text-sm transition-all outline-none resize-none" />
                   </div>
                   
                   <button type="submit" className="group w-full bg-[#3525cd] text-white font-bold py-5 rounded-2xl shadow-xl shadow-[#3525cd]/20 hover:bg-[#1d1b19] transform hover:-translate-y-1 transition-all duration-300 flex items-center justify-center gap-3 text-lg">
                     Request Demo
                     <ArrowIcon />
                   </button>
                 </form>
               </div>
            </div>
          </div>
        )}
      </main>
      
      <footer className="px-6 py-8 text-center relative z-20">
        <p className="text-[#515f74] text-xs font-bold tracking-[0.2em] uppercase opacity-40">© 2026 AuraRecruiting. All rights reserved.</p>
      </footer>
    </div>
  );
}
