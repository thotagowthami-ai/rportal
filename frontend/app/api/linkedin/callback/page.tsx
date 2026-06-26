"use client";

import { useEffect } from "react";

export default function LinkedInCallbackPage() {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");
    const error = params.get("error");
    const error_description = params.get("error_description");

    // Dynamic backend URL extraction from window context if needed, with the production backend as absolute fallback
    let backendBaseUrl = process.env.NEXT_PUBLIC_API_URL || "https://recruitcore-production.up.railway.app";
    
    // If the configured URL is the Railway domain, use the Next.js rewrite proxy to bypass ISP DNS blocks
    if (backendBaseUrl.includes('recruitcore-production.up.railway.app')) {
      backendBaseUrl = window.location.origin + '/api/backend';
    }

    // Construct the redirect URL targeting the backend API callback
    const redirectUrl = new URL(`${backendBaseUrl}/api/linkedin/callback`);
    if (code) redirectUrl.searchParams.set("code", code);
    if (state) redirectUrl.searchParams.set("state", state);
    if (error) redirectUrl.searchParams.set("error", error);
    if (error_description) {
      redirectUrl.searchParams.set("error_description", error_description);
    }

    console.log("Client-side redirecting to backend:", redirectUrl.toString());

    // Securely redirect the browser to the backend callback endpoint
    window.location.href = redirectUrl.toString();
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#fef8f3]">
      <div className="p-8 bg-white rounded-2xl shadow-xl max-w-sm text-center border border-[#e8dfd6]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-[#3525cd] border-t-transparent mx-auto mb-5"></div>
        <h2 className="text-lg font-bold text-[#1d1b19] mb-2">Connecting to LinkedIn</h2>
        <p className="text-sm text-[#515f74] leading-relaxed">
          Please wait while we secure your connection and complete authorization.
        </p>
      </div>
    </div>
  );
}
