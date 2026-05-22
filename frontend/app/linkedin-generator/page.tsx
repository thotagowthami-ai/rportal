"use client";

import { useEffect, useState } from "react";
import { ProtectedRoute } from "@/lib/protected-route";
import api from "@/lib/api";
import { FormattedJobDescription } from "@/components/FormattedJobDescription";
import { toast } from "sonner";

type GenerateResponse = {
  post: string;
  source: "gemini" | "openai" | "deepseek" | "local";
  feedback: string[];
};

type ModelType = "gemini" | "openai" | "deepseek";

type LinkedInStatus = {
  connected: boolean;
  person_urn?: string | null;
  expires_at?: string | null;
};

type LinkedInConnectResponse = { auth_url: string };
type LinkedInPostResponse = { ok: boolean; post_id: string; url: string };

export default function LinkedinGeneratorPage() {
  const [jobDescription, setJobDescription] = useState("");
  const tone = "professional";
  const [model, setModel] = useState<ModelType>("gemini");
  const [post, setPost] = useState("");
  const [source, setSource] = useState<GenerateResponse["source"] | null>(null);
  const [feedback, setFeedback] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [linkedinStatus, setLinkedinStatus] = useState<LinkedInStatus>({ connected: false });
  const [linkedinLoading, setLinkedinLoading] = useState(false);
  const [posting, setPosting] = useState(false);
  const [linkedinMessage, setLinkedinMessage] = useState<string | null>(null);
  const [showAutoPostPrompt, setShowAutoPostPrompt] = useState(false);
  const [copied, setCopied] = useState(false);

  const loadLinkedInStatus = async () => {
    try {
      const res = await api.get<LinkedInStatus>("/api/linkedin/status");
      setLinkedinStatus(res.data);
    } catch {
      setLinkedinStatus({ connected: false });
    }
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const linkedin = params.get("linkedin");
      const reason = params.get("reason");
      if (linkedin === "connected") {
        setLinkedinMessage("LinkedIn connected successfully.");
        toast.success("LinkedIn connected successfully.");
        // Clear the URL params to avoid repeated toasts on refresh
        window.history.replaceState({}, document.title, window.location.pathname);
      } else if (linkedin === "error") {
        const msg =
          reason
            ? "LinkedIn connection failed: " + reason
            : "LinkedIn connection failed.";
        setLinkedinMessage(msg);
        toast.error("LinkedIn connection failed.");
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    }
    loadLinkedInStatus();
  }, []);

  const handleGenerate = async () => {
    if (!jobDescription.trim()) return;
    setLoading(true);
    setError("");
    setPost("");
    setSource(null);
    setFeedback([]);
    setCopied(false);

    try {
      // Refresh status before starting to ensure we have the latest connection info
      await loadLinkedInStatus();

      const res = await api.post<GenerateResponse>("/api/linkedin-posts/generate", {
        input: jobDescription,
        tone,
        model,
      });
      const generatedPost = res.data.post || "";
      setPost(generatedPost);
      setSource(res.data.source || null);
      

      const feedbackItems = Array.isArray(res.data.feedback) ? res.data.feedback : [];
      setFeedback(feedbackItems.filter(f => f !== "Strong structure, tone, and CTA."));
      
      // Final re-check of status right before prompting to be 100% sure
      const statusRes = await api.get<LinkedInStatus>("/api/linkedin/status");
      setLinkedinStatus(statusRes.data);

      if (generatedPost.trim() && statusRes.data.connected) {
        setShowAutoPostPrompt(true);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to generate LinkedIn post";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!post) return;
    await navigator.clipboard.writeText(post);
    setCopied(true);
    if (typeof window !== "undefined") {
      window.setTimeout(() => setCopied(false), 1600);
    }
  };

  const handleConnectLinkedIn = async () => {
    setLinkedinLoading(true);
    setLinkedinMessage(null);
    try {
      const res = await api.post<LinkedInConnectResponse>("/api/linkedin/connect", {
        return_to: "/linkedin-generator",
      });
      window.location.href = res.data.auth_url;
    } catch (err: unknown) {
      setLinkedinMessage(err instanceof Error ? err.message : "Failed to start LinkedIn connection");
      setLinkedinLoading(false);
    }
  };

  const handleDisconnectLinkedIn = async () => {
    setLinkedinLoading(true);
    setLinkedinMessage(null);
    try {
      await api.delete("/api/linkedin/disconnect");
      setLinkedinStatus({ connected: false });
      setLinkedinMessage("LinkedIn disconnected.");
    } catch (err: unknown) {
      setLinkedinMessage(err instanceof Error ? err.message : "Failed to disconnect LinkedIn");
    } finally {
      setLinkedinLoading(false);
    }
  };

  const handlePostToLinkedIn = async () => {
    if (!post.trim()) return;
    if (!linkedinStatus.connected) {
      setLinkedinMessage("Please connect LinkedIn first");
      toast.error("Please connect LinkedIn first");
      return;
    }

    setPosting(true);
    setLinkedinMessage(null);
    try {
      const res = await api.post<LinkedInPostResponse>("/api/linkedin/post", {
        text: formatForLinkedIn(post),
      });
      if (res.data.ok) {
        setLinkedinMessage("Posted to LinkedIn successfully!");
        toast.success("Posted to LinkedIn successfully!");
      }
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Failed to post on LinkedIn";
      setLinkedinMessage(errorMsg);
      toast.error(errorMsg);
    } finally {
      setPosting(false);
    }
  };

  const handlePromptYes = async () => {
    setShowAutoPostPrompt(false);
    await handlePostToLinkedIn();
  };

  const handlePromptNo = () => setShowAutoPostPrompt(false);

  return (
    <ProtectedRoute>
      <div className="bg-[#fef8f3] min-h-screen p-8">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-[#1d1b19]">LinkedIn Generator</h1>
              <p className="text-sm text-[#515f74]">Draft high-performing posts in minutes</p>
            </div>
            <button
              type="button"
              onClick={handlePostToLinkedIn}
              disabled={!post || !linkedinStatus.connected || posting}
              className="px-6 py-2 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-lg font-medium hover:shadow-lg transition-all disabled:opacity-50 text-sm"
            >
              {posting ? "Posting..." : "Post to LinkedIn"}
            </button>
          </div>

          <div className="bg-white rounded-2xl px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3 flex-wrap">
              <div
                className={
                  linkedinStatus.connected
                    ? "w-2 h-2 rounded-full bg-green-500"
                    : "w-2 h-2 rounded-full bg-[#515f74]"
                }
              />
              <span className="text-sm font-semibold text-[#1d1b19]">LinkedIn</span>

              {linkedinStatus.connected ? (
                <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
                  Connected
                  {linkedinStatus.expires_at
                    ? " · Expires " + new Date(linkedinStatus.expires_at).toLocaleDateString()
                    : ""}
                </span>
              ) : (
                <span className="text-xs text-[#515f74]">Not connected</span>
              )}

              {linkedinMessage && (
                <span
                  className={
                    linkedinMessage.includes("success") || linkedinMessage.includes("connected")
                      ? "text-xs text-green-600"
                      : "text-xs text-red-500"
                  }
                >
                  {linkedinMessage}
                </span>
              )}
            </div>

            <div>
              {!linkedinStatus.connected ? (
                <button
                  type="button"
                  onClick={handleConnectLinkedIn}
                  disabled={linkedinLoading}
                  className="px-4 py-2 bg-[#0a66c2] text-white rounded-lg text-sm font-semibold hover:bg-[#0958a8] transition-colors disabled:opacity-50"
                >
                  {linkedinLoading ? "Connecting..." : "Connect LinkedIn"}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleDisconnectLinkedIn}
                  disabled={linkedinLoading}
                  className="px-4 py-2 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg text-sm font-medium hover:bg-[#f8f3ee] transition-colors disabled:opacity-50"
                >
                  {linkedinLoading ? "Disconnecting..." : "Disconnect"}
                </button>
              )}
            </div>
          </div>

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-5">
              <div className="bg-white rounded-2xl p-6">
                <h2 className="text-base font-bold text-[#1d1b19] mb-1">Post Inputs</h2>
                <p className="text-sm text-[#515f74] mb-5">Choose a model and add job details</p>

                <div className="space-y-5">
                  <div>
                    <label className="text-sm font-semibold text-[#1d1b19] block mb-2">
                      AI Model
                    </label>
                    <div className="flex border-b border-[#e8dfd6]">
                      {(["gemini", "openai", "deepseek"] as ModelType[]).map((m) => (
                        <div key={m} className="flex flex-col">
                          <button
                            type="button"
                            onClick={() => setModel(m)}
                            className={
                              model === m
                                ? "px-4 py-2.5 text-sm font-semibold border-b-2 border-[#3525cd] text-[#3525cd] transition-colors"
                                : "px-4 py-2.5 text-sm font-medium border-b-2 border-transparent text-[#515f74] hover:text-[#1d1b19] transition-colors"
                            }
                          >
                            {m === "gemini" ? "✦ Gemini" : m === "openai" ? "◎ OpenAI" : "◈ DeepSeek"}
                          </button>
                        </div>
                      ))}
                    </div>
                    <p className="text-[0.7rem] text-[#515f74] mt-2 italic px-1">
                      {model === "gemini" 
                        ? "✦ Best for speed, creativity and high-converting hooks." 
                        : model === "openai" 
                        ? "◎ Best for nuanced, professional and detailed job descriptions." 
                        : "◈ Best for structured, logical and concise role overviews."}
                    </p>
                  </div>

                  <div>
                    <label className="text-sm font-semibold text-[#1d1b19] block mb-2">
                      Job Description
                    </label>
                    <textarea
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                      rows={10}
                      placeholder="Paste role details, JD, or notes..."
                      className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors resize-none text-sm"
                    />
                  </div>

                  <button
                    type="button"
                    onClick={handleGenerate}
                    disabled={loading || !jobDescription.trim()}
                    className="w-full px-6 py-3 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-lg font-medium hover:shadow-lg transition-all disabled:opacity-50 text-sm"
                  >
                    {loading ? "Generating..." : "Generate LinkedIn Post"}
                  </button>
                </div>
              </div>

              {source && (
                <div className="bg-white rounded-2xl px-6 py-4">
                  <div className="flex items-center gap-3">
                    <span className="px-2.5 py-1 bg-[#3525cd]/10 text-[#3525cd] rounded-full text-xs font-semibold capitalize">
                      {source}
                    </span>
                    <span className="text-sm text-[#515f74]">
                      {feedback.length ? feedback.join(" · ") : "Post generated successfully"}
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div className="bg-white rounded-2xl p-6 flex flex-col">
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h2 className="text-base font-bold text-[#1d1b19]">Preview</h2>
                  <p className="text-sm text-[#515f74]">Your generated LinkedIn post</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleCopy}
                    disabled={!post}
                    className="px-4 py-2 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg text-sm font-medium hover:bg-[#f8f3ee] transition-colors disabled:opacity-50"
                  >
                    {copied ? "✓ Copied!" : "Copy Post"}
                  </button>
                  <button
                    type="button"
                    onClick={handlePostToLinkedIn}
                    disabled={!post || !linkedinStatus.connected || posting}
                    className="px-4 py-2 bg-[#0a66c2] text-white rounded-lg text-sm font-semibold hover:bg-[#0958a8] transition-colors disabled:opacity-50"
                  >
                    {posting ? "Posting..." : "Post Now"}
                  </button>
                </div>
              </div>

              <div className="flex-1 bg-[#f8f3ee] rounded-xl p-5 min-h-[400px] flex flex-col">
                {post ? (
                  <>
                    <div className="flex-1">
                      <FormattedJobDescription content={post} />
                    </div>
                    <div className="mt-4 pt-4 border-t border-[#e8dfd6] flex items-center justify-between">
                      <span className={`text-xs font-medium ${post.length > 2800 ? "text-red-500" : "text-[#515f74]"}`}>
                        {post.length.toLocaleString()} / 3,000 characters
                      </span>
                      {post.length > 3000 && (
                        <span className="text-[10px] text-red-500 font-bold uppercase tracking-wider">Over limit</span>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="h-full min-h-[360px] flex-1 flex flex-col items-center justify-center text-center gap-3">
                    <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center text-2xl shadow-sm">
                      🔗
                    </div>
                    <p className="text-sm font-medium text-[#1d1b19]">Your post will appear here</p>
                    <p className="text-xs text-[#515f74]">
                      Fill in the job description and hit Generate
                    </p>
                  </div>
                )}
              </div>

            </div>
          </div>
        </div>
      </div>

      {showAutoPostPrompt && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl">
            <h3 className="text-xl font-bold text-[#1d1b19] mb-2">Post directly to LinkedIn?</h3>
            <p className="text-sm text-[#515f74] mb-6 leading-relaxed">
              Your post is ready. Do you want to publish it to your connected LinkedIn profile now?
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handlePromptNo}
                className="flex-1 px-4 py-3 bg-white border border-[#e8dfd6] text-[#515f74] rounded-lg font-medium hover:bg-[#f8f3ee] transition-colors text-sm"
              >
                Not Now
              </button>
              <button
                type="button"
                onClick={handlePromptYes}
                className="flex-1 px-4 py-3 bg-[#0a66c2] text-white rounded-lg font-semibold hover:bg-[#0958a8] transition-colors text-sm"
              >
                Yes, Post Now
              </button>
            </div>
          </div>
        </div>
      )}
    </ProtectedRoute>
  );
}

function formatForLinkedIn(text: string): string {
  const boldMap: Record<string, string> = {
    a:"𝗮",b:"𝗯",c:"𝗰",d:"𝗱",e:"𝗲",f:"𝗳",g:"𝗴",h:"𝗵",i:"𝗶",j:"𝗷",k:"𝗸",l:"𝗹",m:"𝗺",
    n:"𝗻",o:"𝗼",p:"𝗽",q:"𝗾",r:"𝗿",s:"𝘀",t:"𝘁",u:"𝘂",v:"𝘃",w:"𝘄",x:"𝘅",y:"𝘆",z:"𝘇",
    A:"𝗔",B:"𝗕",C:"𝗖",D:"𝗗",E:"𝗘",F:"𝗙",G:"𝗚",H:"𝗛",I:"𝗜",J:"𝗝",K:"𝗞",L:"𝗟",M:"𝗠",
    N:"𝗡",O:"𝗢",P:"𝗣",Q:"𝗤",R:"𝗥",S:"𝗦",T:"𝗧",U:"𝗨",V:"𝗩",W:"𝗪",X:"𝗫",Y:"𝗬",Z:"𝗭",
    "0":"𝟬","1":"𝟭","2":"𝟮","3":"𝟯","4":"𝟰","5":"𝟱","6":"𝟲","7":"𝟳","8":"𝟴","9":"𝟵",
  };

  const italicMap: Record<string, string> = {
    a:"𝘢",b:"𝘣",c:"𝘤",d:"𝘥",e:"𝘦",f:"𝘧",g:"𝘨",h:"𝘩",i:"𝘪",j:"𝘫",k:"𝘬",l:"𝘭",m:"𝘮",
    n:"𝘯",o:"𝘰",p:"𝘱",q:"𝘲",r:"𝘳",s:"𝘴",t:"𝘵",u:"𝘶",v:"𝘷",w:"𝘸",x:"𝘹",y:"𝘺",z:"𝘻",
    A:"𝘈",B:"𝘉",C:"𝘊",D:"𝘋",E:"𝘌",F:"𝘍",G:"𝘎",H:"𝘏",I:"𝘐",J:"𝘑",K:"𝘒",L:"𝘓",M:"𝘔",
    N:"𝘕",O:"𝘖",P:"𝘗",Q:"𝘘",R:"𝘙",S:"𝘚",T:"𝘛",U:"𝘜",V:"𝘝",W:"𝘞",X:"𝘟",Y:"𝘠",Z:"𝘡",
  };

  const toBold = (v: string) => v.split("").map((ch) => boldMap[ch] ?? ch).join("");
  const toItalic = (v: string) => v.split("").map((ch) => italicMap[ch] ?? ch).join("");

  return text
    .split("\n")
    .map((line) => {
      const trimmed = line.trim();
      if (trimmed.startsWith("🚀")) return "🚀 " + toBold(trimmed.replace("🚀", "").trim());
      if (trimmed.toLowerCase().includes("tech stack")) return toBold(trimmed);
      return trimmed
        .replace(/\*\*([^*\n]+)\*\*/g, (_: string, value: string) => toBold(value))
        .replace(/\*([^*\n]+)\*/g, (_: string, value: string) => toItalic(value))
        .replace(/_([^_\n]+)_/g, (_: string, value: string) => toItalic(value))
        .replace(/hashtag#/gi, "#")
        .replace(/\bhashtag\b/gi, "#");
    })
    .join("\n");
}