"use client";

import { FormEvent, useState } from "react";
import { ProtectedRoute } from "@/lib/protected-route";
import { useAuth } from "@/lib/auth-context";
import { canManageUsers } from "@/lib/permissions";
import { Modal } from "@/components/ui/Modal";
import { toast } from "sonner";

type CompanyProfile = {
  companyName: string;
  industry: string;
  companySize: string;
  website: string;
};

type UsageData = {
  resumesUsed: number;
  resumesLimit: number;
  matchesUsed: number;
  matchesLimit: number;
  aiUsed: number;
  aiLimit: number;
};

const DEFAULT_PROFILE: CompanyProfile = {
  companyName: "Acme Corp",
  industry: "Technology",
  companySize: "50-100 employees",
  website: "https://acmecorp.com",
};

const DEFAULT_USAGE: UsageData = {
  resumesUsed: 47,
  resumesLimit: 500,
  matchesUsed: 234,
  matchesLimit: 1000,
  aiUsed: 312,
  aiLimit: 1000,
};

const TEAM_SEED = [
  { email: "sarah@acmecorp.com", role: "Admin" },
  { email: "john@acmecorp.com",  role: "Recruiter" },
];

export default function SettingsPage() {
  const { user } = useAuth();
  const isAdmin = canManageUsers(user?.role);

  const [profile, setProfile]                       = useState<CompanyProfile>(DEFAULT_PROFILE);
  const [profileMessage, setProfileMessage]         = useState("");
  const [inviteEmail, setInviteEmail]               = useState("");
  const [inviteRole, setInviteRole]                 = useState<"Recruiter" | "Viewer">("Recruiter");
  const [team, setTeam]                             = useState(TEAM_SEED);
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [slackIntegration, setSlackIntegration]     = useState(false);
  const [linkedInSync, setLinkedInSync]             = useState(false);
  const [atsIntegration, setAtsIntegration]         = useState(false);
  const [integrationModal, setIntegrationModal]     = useState<"slack" | "linkedin" | "ats" | null>(null);
  const [isConnecting, setIsConnecting]             = useState(false);

  const usage = DEFAULT_USAGE;

  const usageItems = [
    { label: "Resume Uploads",    used: usage.resumesUsed,  limit: usage.resumesLimit  },
    { label: "Matches Generated", used: usage.matchesUsed,  limit: usage.matchesLimit  },
    { label: "AI Requests",       used: usage.aiUsed,       limit: usage.aiLimit       },
  ];

  const onSaveProfile = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setProfileMessage("Company profile saved.");
    setTimeout(() => setProfileMessage(""), 3000);
  };

  const onInvite = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    setTeam((prev) => [...prev, { email: inviteEmail.trim(), role: inviteRole }]);
    setInviteEmail("");
    setInviteRole("Recruiter");
  };

  const removeMember = (email: string) => {
    setTeam((prev) => prev.filter((m) => m.email !== email));
  };

  const toggleClass =
    "relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full transition-colors duration-200";

  return (
    <ProtectedRoute>
      <div className="bg-[#fef8f3] min-h-screen p-8">
        <div className="max-w-4xl mx-auto space-y-6">

          {/* Page Header */}
          <div>
            <h1 className="text-xl font-bold text-[#1d1b19]">Settings</h1>
            <p className="text-sm text-[#515f74]">
              Update company details, manage your team, and control integrations
            </p>
          </div>

          {/* Company Profile */}
          <div className="bg-white rounded-2xl p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-base font-bold text-[#1d1b19]">Company Profile</h2>
                <p className="text-sm text-[#515f74]">Basic information about your organisation</p>
              </div>
              {profileMessage && (
                <span className="text-xs font-semibold text-green-600 bg-green-50 px-3 py-1 rounded-full">
                  {profileMessage}
                </span>
              )}
            </div>

            <form onSubmit={onSaveProfile} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-[#515f74] block mb-1.5">
                    Company Name
                  </label>
                  <input
                    className="w-full bg-[#f8f3ee] px-4 py-2.5 rounded-lg text-sm text-[#1d1b19] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors"
                    value={profile.companyName}
                    onChange={(e) => setProfile((p) => ({ ...p, companyName: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[#515f74] block mb-1.5">
                    Industry
                  </label>
                  <select
                    className="w-full bg-[#f8f3ee] px-4 py-2.5 rounded-lg text-sm text-[#1d1b19] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors"
                    value={profile.industry}
                    onChange={(e) => setProfile((p) => ({ ...p, industry: e.target.value }))}
                  >
                    <option>Technology</option>
                    <option>Healthcare</option>
                    <option>Finance</option>
                    <option>Education</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-[#515f74] block mb-1.5">
                    Company Size
                  </label>
                  <select
                    className="w-full bg-[#f8f3ee] px-4 py-2.5 rounded-lg text-sm text-[#1d1b19] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors"
                    value={profile.companySize}
                    onChange={(e) => setProfile((p) => ({ ...p, companySize: e.target.value }))}
                  >
                    <option>1-10 employees</option>
                    <option>11-50 employees</option>
                    <option>50-100 employees</option>
                    <option>101-500 employees</option>
                    <option>500+ employees</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-[#515f74] block mb-1.5">
                    Website
                  </label>
                  <input
                    className="w-full bg-[#f8f3ee] px-4 py-2.5 rounded-lg text-sm text-[#1d1b19] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors"
                    value={profile.website}
                    onChange={(e) => setProfile((p) => ({ ...p, website: e.target.value }))}
                  />
                </div>
              </div>
              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  className="px-6 py-2 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-lg text-sm font-semibold hover:shadow-lg transition-all"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>

          {/* Subscription & Usage */}
          <div className="bg-white rounded-2xl p-6">
            <div className="mb-5">
              <h2 className="text-base font-bold text-[#1d1b19]">Subscription & Usage</h2>
              <p className="text-sm text-[#515f74]">Current plan and usage this month</p>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-5">
              <div className="bg-[#f8f3ee] rounded-xl p-4">
                <p className="text-xs font-semibold text-[#515f74] mb-1">Plan</p>
                <p className="text-sm font-bold text-[#1d1b19]">Pro</p>
                <p className="text-xs text-[#515f74]">$99 / month</p>
              </div>
              <div className="bg-[#f8f3ee] rounded-xl p-4">
                <p className="text-xs font-semibold text-[#515f74] mb-1">Status</p>
                <span className="text-xs font-semibold text-green-600 bg-green-100 px-2 py-0.5 rounded-full">
                  Active
                </span>
              </div>
            </div>

            <p className="text-xs font-semibold text-[#515f74] mb-3 uppercase tracking-wider">
              Usage This Month
            </p>
            <div className="space-y-3 mb-5">
              {usageItems.map((item) => {
                const pct = Math.round((item.used / item.limit) * 100);
                return (
                  <div key={item.label}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-[#1d1b19]">{item.label}</span>
                      <span className="text-xs text-[#515f74]">
                        {item.used} / {item.limit}
                      </span>
                    </div>
                    <div className="h-1.5 bg-[#f8f3ee] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-[#3525cd] to-[#4f46e5] rounded-full"
                        style={{ width: pct + "%" }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                className="px-4 py-2 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg text-sm font-medium hover:bg-[#f8f3ee] transition-colors"
              >
                Upgrade to Enterprise
              </button>
              <button
                type="button"
                className="px-4 py-2 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg text-sm font-medium hover:bg-[#f8f3ee] transition-colors"
              >
                Manage Billing
              </button>
            </div>
          </div>

          {/* Team Members */}
          <div className="bg-white rounded-2xl p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-base font-bold text-[#1d1b19]">Team Members</h2>
                <p className="text-sm text-[#515f74]">Manage who has access to your workspace</p>
              </div>
              {!isAdmin && (
                <span className="text-xs font-semibold text-[#8a5b00] bg-[#fff3d8] px-3 py-1 rounded-full">
                  Admin only
                </span>
              )}
            </div>

            {!isAdmin && (
              <div className="mb-4 p-3 bg-[#fff3d8] rounded-lg text-sm text-[#8a5b00]">
                Only admins can edit team members.
              </div>
            )}

            <div className="space-y-2 mb-5">
              {team.map((member) => (
                <div
                  key={member.email}
                  className="flex items-center justify-between px-4 py-3 bg-[#f8f3ee] rounded-xl"
                >
                  <div>
                    <p className="text-sm font-semibold text-[#1d1b19]">{member.email}</p>
                    <p className="text-xs text-[#515f74]">{member.role}</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      disabled={!isAdmin}
                      className="px-3 py-1.5 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg text-xs font-medium hover:bg-white transition-colors disabled:opacity-40"
                      type="button"
                    >
                      Edit
                    </button>
                    <button
                      disabled={!isAdmin}
                      onClick={() => removeMember(member.email)}
                      className="px-3 py-1.5 bg-white border border-red-200 text-red-500 rounded-lg text-xs font-medium hover:bg-red-50 transition-colors disabled:opacity-40"
                      type="button"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <form onSubmit={onInvite} className="grid grid-cols-3 gap-3">
              <input
                type="email"
                placeholder="team@company.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                disabled={!isAdmin}
                className="col-span-1 bg-[#f8f3ee] px-4 py-2.5 rounded-lg text-sm text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-40"
              />
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value as "Recruiter" | "Viewer")}
                disabled={!isAdmin}
                className="bg-[#f8f3ee] px-4 py-2.5 rounded-lg text-sm text-[#1d1b19] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-40"
              >
                <option>Recruiter</option>
                <option>Viewer</option>
              </select>
              <button
                type="submit"
                disabled={!isAdmin}
                className="px-4 py-2.5 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-lg text-sm font-semibold hover:shadow-lg transition-all disabled:opacity-40"
              >
                + Invite Member
              </button>
            </form>
          </div>

          {/* Integrations */}
          <div className="bg-white rounded-2xl p-6">
            <div className="mb-5">
              <h2 className="text-base font-bold text-[#1d1b19]">Integrations</h2>
              <p className="text-sm text-[#515f74]">Connect tools to your workspace</p>
            </div>

            <div className="space-y-3">
              {[
                {
                  label: "Email Notifications",
                  desc: "Receive alerts for new matches and activity",
                  value: emailNotifications,
                  set: setEmailNotifications,
                },
                {
                  label: "Slack Integration",
                  desc: "Post notifications directly to Slack channels",
                  value: slackIntegration,
                  set: setSlackIntegration,
                },
                {
                  label: "LinkedIn Sync",
                  desc: "Sync candidate profiles from LinkedIn",
                  value: linkedInSync,
                  set: setLinkedInSync,
                },
                {
                  label: "ATS Integration",
                  desc: "Connect Greenhouse, Lever, and other ATS tools",
                  value: atsIntegration,
                  set: setAtsIntegration,
                },
              ].map((item) => (
                <div
                  key={item.label}
                  className="flex items-center justify-between px-4 py-3 bg-[#f8f3ee] rounded-xl"
                >
                  <div>
                    <p className="text-sm font-semibold text-[#1d1b19]">{item.label}</p>
                    <p className="text-xs text-[#515f74]">{item.desc}</p>
                  </div>
                  <button
                    type="button"
                    aria-label={item.label}
                    onClick={() => {
                      if (item.value) {
                        item.set(false);
                      } else {
                        // Special handling for integrations that need setup
                        if (item.label.includes("Slack")) setIntegrationModal("slack");
                        else if (item.label.includes("LinkedIn")) setIntegrationModal("linkedin");
                        else if (item.label.includes("ATS")) setIntegrationModal("ats");
                        else item.set(true);
                      }
                    }}
                    className={
                      toggleClass +
                      (item.value ? " bg-[#3525cd]" : " bg-[#e8dfd6]")
                    }
                    role="switch"
                    aria-checked={item.value}
                  >
                    <span
                      className={
                        "inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform duration-200 " +
                        (item.value ? "translate-x-4" : "translate-x-0.5")
                      }
                    />
                  </button>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
      <Modal
        isOpen={!!integrationModal}
        onClose={() => setIntegrationModal(null)}
        title={
          integrationModal === "slack" ? "Connect to Slack" :
          integrationModal === "linkedin" ? "LinkedIn Sync Setup" :
          "Connect your ATS"
        }
        primaryAction={{
          label: isConnecting ? "Connecting..." : "Connect",
          onClick: async () => {
            setIsConnecting(true);
            // Simulate OAuth/Setup
            await new Promise(r => setTimeout(r, 1500));
            if (integrationModal === "slack") setSlackIntegration(true);
            if (integrationModal === "linkedin") setLinkedInSync(true);
            if (integrationModal === "ats") setAtsIntegration(true);
            setIsConnecting(false);
            setIntegrationModal(null);
            toast.success("Integration connected successfully!");
          },
          loading: isConnecting
        }}
        secondaryAction={{
          label: "Cancel",
          onClick: () => setIntegrationModal(null)
        }}
      >
        <div className="space-y-4">
          <div className="flex items-center gap-3 p-4 bg-[#fdf8f3] rounded-xl border border-[#e8dfd6]">
             <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center text-xl shadow-sm">
               {integrationModal === "slack" ? "💬" : integrationModal === "linkedin" ? "🔗" : "📦"}
             </div>
             <div>
               <p className="text-sm font-bold text-[#1d1b19]">
                 {integrationModal === "slack" ? "Aura for Slack" : integrationModal === "linkedin" ? "LinkedIn Personnel API" : "Greenhouse / Lever Sync"}
               </p>
               <p className="text-[10px] text-[#515f74] uppercase tracking-widest">Available on Pro Plan</p>
             </div>
          </div>
          <p className="text-sm text-[#515f74] leading-relaxed">
            {integrationModal === "slack" 
              ? "Connecting Slack will allow Aura to post match alerts and hiring updates directly to your chosen channels."
              : integrationModal === "linkedin"
              ? "Sync candidate profiles and applications directly from your LinkedIn Recruiter seat."
              : "Automatically pull job descriptions and candidate pipelines from your existing Applicant Tracking System."}
          </p>
          <div className="p-3 bg-blue-50 rounded-lg border border-blue-100 italic text-[11px] text-blue-700">
             You will be redirected to the provider's authorization page to grant Aura access.
          </div>
        </div>
      </Modal>
    </ProtectedRoute>
  );
}