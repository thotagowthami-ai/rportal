"use client";

import { FormEvent, useMemo, useState } from "react";
import Link from "next/link";

type FormErrors = {
  email?: string;
  form?: string;
};

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState("");

  const emailInvalid = useMemo(
    () => email.length > 0 && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email),
    [email]
  );

  const validate = () => {
    const nextErrors: FormErrors = {};
    if (!email.trim()) {
      nextErrors.email = "Email is required";
    } else if (emailInvalid) {
      nextErrors.email = "Enter a valid email address";
    }
    return nextErrors;
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSuccess("");

    const nextErrors = validate();
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    const apiBase = (process.env.NEXT_PUBLIC_API_URL || "").trim();
    const resetUrl = apiBase ? `${apiBase}/api/auth/forgot-password` : "/api/auth/forgot-password";

    try {
      setIsLoading(true);
      setErrors({});

      const res = await fetch(resetUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(
          data?.detail ||
            data?.message ||
            "Password reset isn't available yet. Please contact your admin."
        );
      }

      setSuccess("If an account exists for that email, you'll receive a reset link shortly.");
    } catch (error) {
      setErrors({
        form:
          error instanceof Error
            ? error.message
            : "Password reset isn't available yet. Please contact your admin.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#fdf8f3] text-[#1f2937] font-['Plus_Jakarta_Sans',sans-serif]">
      <header className="border-b border-[#eadfce] bg-[#fdf8f3]/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-10">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#3525cd] text-xs font-black text-white shadow-md">
              A
            </div>
            <div>
              <p className="text-sm font-extrabold tracking-[0.18em] uppercase text-[#3525cd]">
                AuraRecruiting
              </p>
              <p className="text-xs text-[#6b7280]">Hiring intelligence platform</p>
            </div>
          </Link>

          <Link
            href="/login"
            className="rounded-xl border border-[#d8cfbf] px-4 py-2 text-sm font-bold text-[#1f2937] transition hover:border-[#3525cd] hover:text-[#3525cd]"
          >
            Back to login
          </Link>
        </div>
      </header>

      <main className="mx-auto flex min-h-[calc(100vh-73px)] max-w-7xl items-center justify-center px-6 py-12 lg:px-10">
        <div className="w-full max-w-md rounded-[2rem] border border-[#eadfce] bg-white p-7 shadow-[0_20px_60px_rgba(32,24,12,0.08)] sm:p-8">
          <p className="text-xs font-extrabold uppercase tracking-[0.24em] text-[#3525cd]">
            Reset password
          </p>
          <h1 className="mt-3 text-3xl font-black tracking-tight text-[#111827]">
            Get back into your workspace
          </h1>
          <p className="mt-3 text-sm leading-6 text-[#6b7280]">
            Enter your work email and we will send a reset link if the account exists.
          </p>

          <form className="mt-6 space-y-5" onSubmit={handleSubmit} noValidate>
            <div>
              <label htmlFor="email" className="mb-2 block text-sm font-bold text-[#374151]">
                Work email
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
                  if (!email.trim()) {
                    setErrors((prev) => ({ ...prev, email: "Email is required" }));
                  } else if (emailInvalid) {
                    setErrors((prev) => ({ ...prev, email: "Enter a valid email address" }));
                  }
                }}
                placeholder="you@company.com"
                className={`h-12 w-full rounded-xl border px-4 outline-none transition ${
                  errors.email
                    ? "border-red-500 bg-red-50 text-red-900 placeholder:text-red-300 focus:ring-2 focus:ring-red-200"
                    : "border-[#d8cfbf] bg-[#fffdf9] text-[#111827] placeholder:text-[#9ca3af] focus:border-[#3525cd] focus:ring-2 focus:ring-[#dcd6ff]"
                }`}
              />
              {errors.email ? (
                <p className="mt-2 text-sm font-medium text-red-600">{errors.email}</p>
              ) : null}
            </div>

            {errors.form ? (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                {errors.form}
              </div>
            ) : null}

            {success ? (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
                {success}
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
              {isLoading ? "Sending..." : "Send reset link"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
