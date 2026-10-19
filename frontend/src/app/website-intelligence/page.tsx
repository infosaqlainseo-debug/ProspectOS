"use client";

import { Globe } from "lucide-react";
import Link from "next/link";

export default function WebsiteIntelligencePage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">Website Intelligence</h1>
      </div>

      <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-8 text-center">
        <Globe className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900">No global Website Intelligence endpoint</h3>
        <p className="mt-2 text-sm text-gray-500 max-w-md mx-auto">
          The backend currently only supports fetching website metadata per-company. 
          Please navigate to a specific company in the <Link href="/companies" className="text-blue-600 hover:underline">Companies view</Link> to see its website scan details.
        </p>
      </div>
    </div>
  );
}
