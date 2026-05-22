import {
  canManageJobs,
  canReviewMatches,
  canUploadResumes,
  normalizeRole,
} from "./permissions";

describe("permissions", () => {
  it("normalizes known roles", () => {
    expect(normalizeRole("ADMIN")).toBe("admin");
    expect(normalizeRole(" recruiter ")).toBe("recruiter");
    expect(normalizeRole("viewer")).toBe("viewer");
  });

  it("defaults unknown role safely", () => {
    expect(normalizeRole("something-else")).toBe("unknown");
    expect(normalizeRole(undefined)).toBe("unknown");
  });

  it("allows only admin to manage jobs", () => {
    expect(canManageJobs("admin")).toBe(true);
    expect(canManageJobs("recruiter")).toBe(false);
    expect(canManageJobs("viewer")).toBe(false);
  });

  it("allows admin and recruiter to review matches", () => {
    expect(canReviewMatches("admin")).toBe(true);
    expect(canReviewMatches("recruiter")).toBe(true);
    expect(canReviewMatches("viewer")).toBe(false);
  });

  it("allows admin and recruiter to upload resumes", () => {
    expect(canUploadResumes("admin")).toBe(true);
    expect(canUploadResumes("recruiter")).toBe(true);
    expect(canUploadResumes("viewer")).toBe(false);
  });
});
