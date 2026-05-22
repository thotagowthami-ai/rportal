"use client";

import { ProtectedRoute } from "@/lib/protected-route";

export default function UsersPage() {
  return (
    <ProtectedRoute>
      <div className="bg-[#fef8f3] min-h-screen p-8 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-[#1d1b19]">Users Management</h1>
          <p className="text-[#515f74] mt-2">This module is currently under construction.</p>
        </div>
      </div>
    </ProtectedRoute>
  );
}
