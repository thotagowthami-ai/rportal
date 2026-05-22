"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import axios from "axios";
import { PublicOnlyRoute } from "@/lib/protected-route";

export default function SignupPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({ name: "", email: "", password: "", confirmPassword: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.password) {
      toast.error("Please fill in all fields");
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const apiBase = (process.env.NEXT_PUBLIC_API_URL || "").trim();
      const registerUrl = apiBase ? `${apiBase}/api/auth/register` : "/api/auth/register";

      await axios.post(registerUrl, {
        full_name: formData.name,
        email: formData.email,
        password: formData.password,
        tenant_name: `${formData.name}'s Organization`,
        tenant_slug: formData.name.toLowerCase().replace(/\s+/g, '-') + '-' + Math.random().toString(36).substring(2, 7)
      });
      toast.success("Account created successfully!");
      router.push("/login");
    } catch (err) {
      const errorMessage = "Failed to create account";
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <PublicOnlyRoute>
      <div className="min-h-screen bg-[#fef8f3]">
        <nav className="sticky top-0 z-50 bg-[#fef8f3]/80 backdrop-blur-[20px]">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <Link href="/" className="text-2xl font-bold text-[#3525cd]">AuraRecruiting</Link>
            <div className="flex gap-3">
              <Link href="/" className="text-sm text-[#515f74] hover:text-[#3525cd]">Back Home</Link>
              <Link href="/login" className="px-4 py-2 bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white rounded-full text-sm font-medium">
                Sign In
              </Link>
            </div>
          </div>
        </nav>

        <section className="px-4 sm:px-6 lg:px-8 py-20">
          <div className="mx-auto max-w-md space-y-8">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold text-[#1d1b19]">Create Account</h1>
              <p className="text-[#515f74]">Join the next generation of hiring</p>
            </div>

            <div className="bg-white rounded-2xl p-8 space-y-6">
              {error && (
                <div className="bg-[#7e3000]/10 text-[#7e3000] p-4 rounded-lg text-sm">{error}</div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Full Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    disabled={loading}
                    placeholder="John Doe"
                    className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                  />
                </div>

                <div>
                  <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    disabled={loading}
                    placeholder="you@company.com"
                    className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                  />
                </div>

                <div>
                  <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Password</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    disabled={loading}
                    placeholder="••••••••"
                    className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                  />
                </div>

                <div>
                  <label className="text-sm font-semibold text-[#1d1b19] block mb-2">Confirm Password</label>
                  <input
                    type="password"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                    disabled={loading}
                    placeholder="••••••••"
                    className="w-full bg-[#f8f3ee] px-4 py-3 rounded-lg text-[#1d1b19] placeholder-[#515f74] focus:outline-none focus:ring-2 focus:ring-[#3525cd] focus:bg-white transition-colors disabled:opacity-50"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-br from-[#3525cd] to-[#4f46e5] text-white py-3 rounded-full font-medium hover:shadow-[0_32px_64px_rgba(79,70,229,0.12)] transition-all hover:scale-105 disabled:opacity-50"
                >
                  {loading ? "Creating Account..." : "Create Account"}
                </button>
              </form>

              <p className="text-center text-sm text-[#515f74]">
                Already have an account? <Link href="/login" className="text-[#3525cd] font-medium hover:underline">Sign in</Link>
              </p>
            </div>
          </div>
        </section>
      </div>
    </PublicOnlyRoute>
  );
}