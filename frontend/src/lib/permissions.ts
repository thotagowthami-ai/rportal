export type AppRole = "admin" | "recruiter" | "viewer" | "unknown";

export function normalizeRole(role?: string | null): AppRole {
  const value = (role || "").toLowerCase().trim();
  if (value === "admin") return "admin";
  if (value === "recruiter") return "recruiter";
  if (value === "viewer") return "viewer";
  return "unknown";
}

export function canManageJobs(role?: string | null): boolean {
  const normalized = normalizeRole(role);
  return normalized === "admin" || normalized === "recruiter";
}

export function canReviewMatches(role?: string | null): boolean {
  const normalized = normalizeRole(role);
  return normalized === "admin" || normalized === "recruiter";
}

export function canUploadResumes(role?: string | null): boolean {
  const normalized = normalizeRole(role);
  return normalized === "admin" || normalized === "recruiter";
}

export function canManageUsers(role?: string | null): boolean {
  return normalizeRole(role) === "admin";
}
