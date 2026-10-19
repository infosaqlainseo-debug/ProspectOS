"use client";

import { ShieldAlert } from "lucide-react";

export default function ContradictionsPage() {
  // Assuming a generic contradictions endpoint exists or fetching per company.
  // We'll just show an empty state for now since the backend doesn't have a global /contradictions endpoint yet.
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">AI Contradictions Review</h1>
      </div>

      <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-8 text-center">
        <ShieldAlert className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900">No global contradiction endpoint</h3>
        <p className="mt-2 text-sm text-gray-500">
          The backend currently only supports fetching contradictions per-company. 
          Please navigate to a specific company to view its contradictions.
        </p>
      </div>
    </div>
  );
}
