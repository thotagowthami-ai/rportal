"use client";

import { FormEvent, Suspense, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

type FormErrors = {
  password?: string;
  confirmPassword?: string;
  form?: string;
};

function ResetPasswordContent() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const searchParams = useSearchParams();
  const token = useMemo(() => {
    const t =
      searchParams.get("token") ||
      searchParams.get("reset_token") ||
      searchParams.get("t");
    return t ? t.trim() : null;
  }, [searchParams]);

  const validate = () => {
    const nextErrors: FormErrors = {};
    if (!password.trim()) {
      nextErrors.password = "Password is required";
    } else if (password.length < 8) {
      nextErrors.password = "Password must be at least 8 characters";
    }

    if (password !== confirmPassword) {
      nextErrors.confirmPassword = "Passwords do not match";
    }
    return nextErrors;
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!token) {
      setErrors({ form: "No reset token found. Please use the link from your email." });
      return;
    }

    const nextErrors = validate();
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    try {
      setIsLoading(true);
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });

      const data = await res.json().catch(() => null);

      if (!res.ok) {
        let errorMsg = "Failed to reset password. The link may have expired.";
        
        if (data?.detail) {
          if (typeof data.detail === "string") {
            errorMsg = data.detail;
          } else if (Array.isArray(data.detail) && data.detail[0]?.msg) {
            // Handle FastAPI validation error list
            errorMsg = data.detail[0].msg;
          } else {
            errorMsg = JSON.stringify(data.detail);
          }
        }
        
        setErrors({ form: errorMsg });
        return;
      }

      setIsSuccess(true);
      // Wait bit then redirect
      setTimeout(() => {
        window.location.href = "/login";
      }, 3000);
    } catch (error) {
      setErrors({ form: "Something went wrong. Please try again later." });
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen bg-[#fdf8f3] flex items-center justify-center p-6">
        <div className="w-full max-w-md bg-white rounded-[2rem] border border-[#eadfce] p-8 text-center shadow-xl">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            ✅
          </div>
          <h1 className="text-2xl font-black text-[#111827] mb-2">Password Updated!</h1>
          <p className="text-[#6b7280] mb-6">Your password has been successfully reset. Redirecting you to login...</p>
          <Link href="/login" className="text-[#3525cd] font-bold hover:underline">
            Go to Login now
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#fdf8f3] text-[#1f2937] font-['Plus_Jakarta_Sans',sans-serif]">
      <header className="border-b border-[#d8cfbf] bg-[#fdf8f3]/95 backdrop-blur">
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
        </div>
      </header>

      <main className="mx-auto flex min-h-[calc(100vh-73px)] max-w-7xl items-center justify-center px-6 py-12 lg:px-10">
        <div className="w-full max-w-md rounded-[2rem] border border-[#eadfce] bg-white p-7 shadow-[0_20px_60px_rgba(32,24,12,0.08)] sm:p-8">
          <p className="text-xs font-extrabold uppercase tracking-[0.24em] text-[#3525cd]">
            Security
          </p>
          <h1 className="mt-3 text-3xl font-black tracking-tight text-[#111827]">
            Set new password
          </h1>
          <p className="mt-3 text-sm leading-6 text-[#6b7280]">
            Please enter a secure new password for your account.
          </p>

          <form className="mt-6 space-y-5" onSubmit={handleSubmit} noValidate>
            <div>
              <label htmlFor="password" className="mb-2 block text-sm font-bold text-[#374151]">
                New Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  className={`h-12 w-full rounded-xl border px-4 pr-12 outline-none transition ${
                    errors.password
                      ? "border-red-500 bg-red-50 focus:ring-red-200"
                      : "border-[#d8cfbf] bg-[#fffdf9] focus:border-[#3525cd] focus:ring-[#dcd6ff]"
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-[#9ca3af]"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
              {errors.password && <p className="mt-2 text-sm text-red-600 font-medium">{errors.password}</p>}
            </div>

            <div>
              <label htmlFor="confirm-password" className="mb-2 block text-sm font-bold text-[#374151]">
                Confirm Password
              </label>
              <input
                id="confirm-password"
                name="confirm-password"
                type={showPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat your password"
                className={`h-12 w-full rounded-xl border px-4 outline-none transition ${
                  errors.confirmPassword
                    ? "border-red-500 bg-red-50 focus:ring-red-200"
                    : "border-[#d8cfbf] bg-[#fffdf9] focus:border-[#3525cd] focus:ring-[#dcd6ff]"
                }`}
              />
              {errors.confirmPassword && (
                <p className="mt-2 text-sm text-red-600 font-medium">{errors.confirmPassword}</p>
              )}
            </div>

            {errors.form && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                {errors.form}
              </div>
            )}

            {!token && (
              <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-700">
                ⚠️ Warning: No reset token detected in URL. This page will not work without a valid link.
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || !token}
              className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#3525cd] px-4 text-sm font-bold text-white shadow-[0_14px_24px_rgba(53,37,205,0.22)] transition hover:bg-[#2418a5] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "Saving..." : "Update Password"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#fdf8f3]" />}>
      <ResetPasswordContent />
    </Suspense>
  );
}
