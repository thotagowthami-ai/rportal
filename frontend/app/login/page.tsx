"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

type FormErrors = {
  email?: string;
  password?: string;
  form?: string;
};

export default function LoginPage() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  
  // Touched states to prevent showing errors too early
  const [emailTouched, setEmailTouched] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [isSubmitAttempted, setIsSubmitAttempted] = useState(false);

  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  const searchParams = useSearchParams();
  useEffect(() => {
    const oauthError = searchParams.get("error");
    if (!oauthError) return;
    const messages: Record<string, string> = {
      google_session_expired: "Your sign-in session expired. Please try again.",
      google_no_code: "Google sign-in was cancelled or failed. Please try again.",
      google_invalid_state: "Invalid sign-in request. Please try again.",
      google_token_failed: "Could not complete Google sign-in. Please try again.",
      google_no_email: "Google did not share your email address. Please check your Google account permissions.",
      google_unexpected: "An unexpected error occurred during sign-in. Please try again.",
    };
    setErrors({ form: messages[oauthError] ?? "Google sign-in failed. Please try again." });
    // Clean the error param from the URL without a re-navigation
    const url = new URL(window.location.href);
    url.searchParams.delete("error");
    window.history.replaceState({}, "", url.toString());
  }, [searchParams]);

  const emailInvalid = useMemo(
    () => email.length > 0 && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email),
    [email]
  );

  const validate = () => {
    const nextErrors: FormErrors = {};

    if (!email.trim()) {
      nextErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      nextErrors.email = "Enter a valid email address";
    }

    if (!password.trim()) {
      nextErrors.password = "Password is required";
    }

    return nextErrors;
  };

  const handleGoogleSignIn = () => {
    if (!apiBaseUrl) {
      setErrors({
        form: "Authentication service is not configured.",
      });
      return;
    }

    try {
      setGoogleLoading(true);
      window.location.href = `${apiBaseUrl}/api/auth/google`;
    } catch {
      setErrors({
        form: "Google sign-in is not available right now.",
      });
      setGoogleLoading(false);
    }
  };

  const handleCredentialSignIn = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitAttempted(true);

    const nextErrors = validate();
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) return;

    if (!apiBaseUrl) {
      setErrors({
        form: "Authentication service is not configured.",
      });
      return;
    }

    try {
      setIsLoading(true);
      setErrors({});

      const res = await fetch(
        `${apiBaseUrl}/api/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email,
            password,
          }),
        }
      );

      const data = await res.json().catch(() => null);

      if (!res.ok) {
        setErrors({
          form: data?.detail || data?.message || "Incorrect email or password",
        });
        return;
      }

      // Save token so ProtectedRoute/auth-context can authenticate on next page
      if (data?.access_token) {
        localStorage.setItem("token", data.access_token);
      }
      if (data?.user) {
        localStorage.setItem("user", JSON.stringify(data.user));
      }

      window.location.href = "/dashboard";
    } catch {
      setErrors({
        form: "Something went wrong. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Helper to determine if we should show an error for the email field
  const shouldShowEmailError = (isSubmitAttempted || emailTouched) && errors.email;
  // Helper to determine if we should show an error for the password field
  const shouldShowPasswordError = (isSubmitAttempted || passwordTouched) && errors.password;

  return (
    <div className="min-h-screen bg-[#fdf8f3] text-[#1f2937] font-sans">
      <header className="border-b border-[#d8cfbf] bg-[#fdf8f3]/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-10">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#3525cd] text-xs font-black text-white shadow-md transition-transform group-hover:scale-105">
              A
            </div>
            <div>
              <p className="text-sm font-extrabold tracking-[0.18em] uppercase text-[#3525cd]">
                AuraRecruiting
              </p>
              <p className="text-xs text-[#6b7280]">Hiring intelligence platform</p>
            </div>
          </Link>

          <div className="hidden sm:flex items-center gap-6">
            <Link
              href="/"
              className="text-sm font-semibold text-[#515f74] hover:text-[#1d1b19] transition-colors"
            >
              ← Back to Home
            </Link>
            <p className="text-sm text-[#6b7280]">
              Don&apos;t have an account?{" "}
              <Link href="/signup" className="font-bold text-[#3525cd] hover:underline">
                Create account
              </Link>
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto grid min-h-[calc(100vh-73px)] max-w-7xl grid-cols-1 gap-10 px-6 py-10 lg:grid-cols-2 lg:px-10 lg:py-14">
        {/* Left Section - Feature Showcase */}
        <section className="relative flex flex-col justify-center rounded-[2rem] bg-gradient-to-br from-[#2f1fae] via-[#3525cd] to-[#5d4fff] p-8 text-white shadow-[0_30px_80px_rgba(53,37,205,0.22)] lg:p-12 min-h-[500px]">
          {/* Brand Reinforcement Logo */}
          <div className="absolute top-10 left-10 lg:top-12 lg:left-12 flex items-center gap-3">
             <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/20 text-xs font-black text-white shadow-md backdrop-blur-md border border-white/20">
               A
             </div>
             <div>
               <p className="text-sm font-black tracking-[0.18em] uppercase text-white">
                 AuraRecruiting
               </p>
             </div>
          </div>

          <div className="relative mt-12 lg:mt-6">
            <span className="mb-5 inline-flex w-fit rounded-full border border-white/20 bg-white/10 px-4 py-1 text-xs font-bold uppercase tracking-[0.22em]">
              Welcome back
            </span>

            <h1 className="max-w-xl text-4xl font-black leading-tight lg:text-5xl">
              Sign in to manage hiring faster and smarter.
            </h1>

            <p className="mt-5 max-w-xl text-[1.02rem] leading-7 text-white/82">
              Review candidates, rank resumes, and collaborate with your team from one
              clean recruiting workspace.
            </p>

            {/* Feature Grid with Adjusted Spacing to Prevent Clipping */}
            <div className="mt-10 grid gap-4 grid-cols-1 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur-sm lg:p-5">
                <p className="text-sm font-extrabold">Secure</p>
                <p className="mt-2 text-xs leading-5 text-white/78 lg:text-sm lg:leading-6">
                  Protected access for recruiters, teams, and admins.
                </p>
              </div>

              <div className="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur-sm lg:p-5">
                <p className="text-sm font-extrabold">Fast</p>
                <p className="mt-2 text-xs leading-5 text-white/78 lg:text-sm lg:leading-6">
                  Move from login to candidate review in seconds.
                </p>
              </div>

              <div className="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur-sm lg:p-5">
                <p className="text-sm font-extrabold">AI-Powered</p>
                <p className="mt-2 text-xs leading-5 text-white/78 lg:text-sm lg:leading-6">
                  Score resumes and surface top-fit talent automatically.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Right Section - Sign In Form */}
        <section className="flex items-center justify-center">
          <div className="w-full max-w-md rounded-[2rem] border border-[#eadfce] bg-white p-7 shadow-[0_20px_60px_rgba(32,24,12,0.08)] sm:p-8">
            <p className="text-xs font-extrabold uppercase tracking-[0.24em] text-[#3525cd]">
              Welcome back ✨
            </p>

            <h2 className="mt-3 text-3xl font-black tracking-tight text-[#111827]">
              Access your workspace
            </h2>

            <p className="mt-3 text-sm leading-6 text-[#6b7280]">
              Continue with Google or use your email and password.
            </p>

            <div className="mt-6">
              <button
                type="button"
                onClick={handleGoogleSignIn}
                disabled={googleLoading || isLoading}
                className="flex h-12 w-full items-center justify-center gap-3 rounded-xl border border-[#d8cfbf] bg-white px-4 text-sm font-bold text-[#1f2937] transition hover:border-[#3525cd] hover:bg-[#faf7ff] hover:shadow-sm disabled:cursor-not-allowed disabled:opacity-60"
              >
                {googleLoading ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#3525cd] border-t-transparent" />
                ) : (
                  <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true">
                    <path
                      fill="#EA4335"
                      d="M12 10.2v3.9h5.4c-.2 1.3-1.5 3.9-5.4 3.9-3.2 0-5.9-2.7-5.9-6s2.7-6 5.9-6c1.8 0 3.1.8 3.8 1.4l2.6-2.5C16.7 3.4 14.6 2.5 12 2.5A9.5 9.5 0 0 0 2.5 12 9.5 9.5 0 0 0 12 21.5c5.5 0 9.1-3.9 9.1-9.3 0-.6-.1-1.1-.2-1.9H12Z"
                    />
                  </svg>
                )}
                {googleLoading ? "Connecting..." : "Continue with Google"}
              </button>
            </div>

            {/* Styled Divider with Better Visibility */}
            <div className="relative my-8">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-[#d8cfbf]" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-white px-4 text-[10px] font-black uppercase tracking-[0.25em] text-[#9ca3af]">
                  Or sign in with email
                </span>
              </div>
            </div>

            <form className="space-y-5" onSubmit={handleCredentialSignIn} noValidate>
              <div>
                <label htmlFor="email" className="mb-2 block text-sm font-bold text-[#374151]">
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (errors.email || errors.form) {
                      setErrors((prev) => ({ ...prev, email: undefined, form: undefined }));
                    }
                  }}
                  onBlur={() => {
                    setEmailTouched(true);
                    if (!email.trim()) {
                      setErrors((prev) => ({ ...prev, email: "Email is required" }));
                    } else if (emailInvalid) {
                      setErrors((prev) => ({ ...prev, email: "Enter a valid email address" }));
                    }
                  }}
                  placeholder="name@company.com"
                  className={`h-12 w-full rounded-xl border px-4 outline-none transition ${
                    shouldShowEmailError
                      ? "border-red-500 bg-red-50 text-red-900 placeholder:text-red-300 focus:ring-2 focus:ring-red-200"
                      : "border-[#d8cfbf] bg-[#fffdf9] text-[#111827] placeholder:text-[#9ca3af] focus:border-[#3525cd] focus:ring-2 focus:ring-[#dcd6ff]"
                  }`}
                />
                {shouldShowEmailError ? (
                  <p className="mt-2 text-sm font-medium text-red-600">{errors.email}</p>
                ) : null}
              </div>

              <div>
                <div className="mb-2 flex items-center justify-between gap-3">
                  <label htmlFor="password" className="block text-sm font-bold text-[#374151]">
                    Password
                  </label>
                  <Link
                    href="/forgot-password"
                    className="relative z-10 text-sm font-bold text-[#3525cd] transition hover:text-[#2418a5] hover:underline"
                  >
                    Forgot password?
                  </Link>
                </div>

                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (errors.password || errors.form) {
                        setErrors((prev) => ({ ...prev, password: undefined, form: undefined }));
                      }
                    }}
                    onBlur={() => {
                      setPasswordTouched(true);
                      if (!password.trim()) {
                        setErrors((prev) => ({ ...prev, password: "Password is required" }));
                      }
                    }}
                    placeholder="Enter your password"
                    className={`h-12 w-full rounded-xl border px-4 pr-12 outline-none transition ${
                      shouldShowPasswordError
                        ? "border-red-500 bg-red-50 text-red-900 placeholder:text-red-300 focus:ring-2 focus:ring-red-200"
                        : "border-[#d8cfbf] bg-[#fffdf9] text-[#111827] placeholder:text-[#9ca3af] focus:border-[#3525cd] focus:ring-2 focus:ring-[#dcd6ff]"
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-[#9ca3af] transition hover:text-[#3525cd]"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? (
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-5 w-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                      </svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-5 w-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.01 9.963 7.183a1.015 1.015 0 010 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.01-9.963-7.183z" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    )}
                  </button>
                </div>
                {shouldShowPasswordError ? (
                  <p className="mt-2 text-sm font-medium text-red-600">{errors.password}</p>
                ) : null}
              </div>

              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="h-4 w-4 rounded border-[#d8cfbf] text-[#3525cd] focus:ring-[#3525cd] cursor-pointer transition"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm font-medium text-[#4b5563] cursor-pointer hover:text-[#111827] transition-colors">
                  Remember me for 30 days
                </label>
              </div>

              {errors.form ? (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                  {errors.form}
                </div>
              ) : null}

              <button
                type="submit"
                disabled={isLoading}
                className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#3525cd] px-4 text-sm font-bold text-white shadow-[0_14px_24px_rgba(53,37,205,0.22)] transition hover:bg-[#2418a5] hover:shadow-[0_18px_28px_rgba(53,37,205,0.26)] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isLoading ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/90 border-t-transparent" />
                ) : null}
                {isLoading ? "Signing in..." : "Sign In"}
              </button>
            </form>

            <p className="mt-8 text-center text-sm text-[#6b7280]">
              New to AuraRecruiting?{" "}
              <Link href="/signup" className="font-extrabold text-[#3525cd] hover:underline">
                Create account
              </Link>
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
