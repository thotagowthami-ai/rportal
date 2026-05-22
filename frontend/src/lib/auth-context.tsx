"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

type User = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id: string;
};

type AuthContextType = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (
    email: string,
    password: string,
    fullName: string,
    tenantName: string
  ) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || undefined;

function makeTenantSlug(input: string): string {
  return input
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .slice(0, 60);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      let activeToken = null;

      if (typeof window !== "undefined") {
        const params = new URLSearchParams(window.location.search);
        const urlCode = params.get("code");

        if (urlCode && API_BASE_URL) {
          try {
            const response = await fetch(`${API_BASE_URL}/api/auth/exchange-code`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({ code: urlCode }),
            });
            if (response.ok) {
              const data = await response.json();
              window.localStorage.setItem("token", data.access_token);
              activeToken = data.access_token;
              setUser(data.user);
              // Clean the code from the URL, then navigate to dashboard
              window.history.replaceState({}, document.title, "/dashboard");
              setLoading(false);
              return;
            } else {
              console.error("Code exchange failed:", response.status);
            }
          } catch (e) {
            console.error("Failed to exchange one-time login code:", e);
          } finally {
            // Always remove the code param so it cannot be replayed on refresh
            if (window.location.search.includes("code=")) {
              const newUrl = window.location.pathname;
              window.history.replaceState({}, document.title, newUrl);
            }
          }
        }
      }

      if (!API_BASE_URL) {
        console.error("NEXT_PUBLIC_API_URL is missing. Authentication checks are disabled.");
        setLoading(false);
        return;
      }

      const token = activeToken || window.localStorage.getItem("token");
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          window.localStorage.removeItem("token");
          setUser(null);
          setLoading(false);
          return;
        }

        const data = (await response.json()) as User;
        setUser(data);
      } catch {
        window.localStorage.removeItem("token");
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    if (!API_BASE_URL) {
      console.error("NEXT_PUBLIC_API_URL is missing. Login aborted.");
      throw new Error("Application configuration error: NEXT_PUBLIC_API_URL is missing.");
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || "Login failed");
    }

    const data = await response.json();
    window.localStorage.setItem("token", data.access_token);
    setUser(data.user);
  };

  const signup = async (
    email: string,
    password: string,
    fullName: string,
    tenantName: string
  ) => {
    if (!API_BASE_URL) {
      console.error("NEXT_PUBLIC_API_URL is missing. Signup aborted.");
      throw new Error("Application configuration error: NEXT_PUBLIC_API_URL is missing.");
    }

    const tenantSlug = makeTenantSlug(tenantName) || `org-${Date.now()}`;
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
        tenant_name: tenantName,
        tenant_slug: tenantSlug,
      }),
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || "Registration failed");
    }

    const data = await response.json();
    window.localStorage.setItem("token", data.access_token);
    setUser(data.user);
  };

  const logout = () => {
    window.localStorage.removeItem("token");
    setUser(null);
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
