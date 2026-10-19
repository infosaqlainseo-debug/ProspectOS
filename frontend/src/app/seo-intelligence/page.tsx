"use client";

import { LineChart } from "lucide-react";
import Link from "next/link";

export default function SeoIntelligencePage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">SEO Intelligence</h1>
      </div>

      <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-8 text-center">
        <LineChart className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900">No global SEO endpoint</h3>
        <p className="mt-2 text-sm text-gray-500 max-w-md mx-auto">
          The backend currently only supports fetching SEO metrics per-company. 
          Please navigate to a specific company in the <Link href="/companies" className="text-blue-600 hover:underline">Companies view</Link> to see its SEO metrics.
        </p>
      </div>
    </div>
  );
}
