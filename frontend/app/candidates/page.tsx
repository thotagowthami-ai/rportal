"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function CandidatesRedirect() {
  const router = useRouter();
  useEffect(() => { router.replace("/resumes"); }, [router]);
  return null;
}