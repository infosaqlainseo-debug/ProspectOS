"use client";

import { useState } from "react";
import { useApi, Company } from "@/lib/api";
import Link from "next/link";
import { Search, Filter, Loader2, ArrowRight, ChevronLeft, ChevronRight, Building2, Globe } from "lucide-react";

export default function CompaniesPage() {
  const [query, setQuery] = useState("");
  const [stage, setStage] = useState("");
  const [page, setPage] = useState(0);
  const pageSize = 25;

  // Build query string
  const params = new URLSearchParams();
  if (query) params.append("q", query);
  if (stage) params.append("sales_stage", stage);
  params.append("skip", String(page * pageSize));
  params.append("limit", String(pageSize));
  params.append("sort_by", "created_at");
  params.append("order", "desc");

  const { data, isLoading, error } = useApi<{ total: number; items: Company[] }>(
    `/companies?${params.toString()}`
  );

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Prospect Directory</h1>
          <p className="text-sm text-gray-500 mt-1">
            Real enterprise companies tracked, analyzed, and qualified within ProspectOS.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            href="/discovery"
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            + Import / Discover Prospect
          </Link>
        </div>
      </div>
      
      {/* Search & Filter Toolbar */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative flex-1 w-full">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="Search by company name or domain..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(0);
            }}
          />
        </div>

        <div className="flex items-center space-x-3 w-full md:w-auto">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-500 whitespace-nowrap">Stage:</span>
          </div>
          <select
            value={stage}
            onChange={(e) => {
              setStage(e.target.value);
              setPage(0);
            }}
            className="block w-full md:w-48 pl-3 pr-8 py-2 text-sm border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md border"
          >
            <option value="">All Stages</option>
            <option value="lead">Lead</option>
            <option value="contacted">Contacted</option>
            <option value="discovery">Discovery</option>
            <option value="proposal">Proposal</option>
            <option value="won">Won / Closed</option>
            <option value="lost">Lost</option>
          </select>
        </div>
      </div>

      {/* Directory Table */}
      <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-500">
            Failed to load companies. Backend unavailable.
          </div>
        ) : data?.items.length === 0 ? (
          <div className="p-16 text-center text-gray-500">
            <Building2 className="w-12 h-12 mx-auto text-gray-400 mb-3" />
            <p className="text-lg font-medium text-gray-900">No companies found</p>
            <p className="mt-1 text-sm text-gray-500">
              {query || stage ? "Try adjusting your search query or filters." : "Use the Discovery tool to import or find new prospects."}
            </p>
            <Link
              href="/discovery"
              className="mt-4 inline-flex items-center px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700"
            >
              Go to Intake & Discovery &rarr;
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Company
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Canonical Domain
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Industry
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sales Stage
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Discovered
                  </th>
                  <th scope="col" className="relative px-6 py-3">
                    <span className="sr-only">View</span>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data?.items.map((company) => {
                  const companyName = company.company_name || company.name || "Unnamed Company";
                  const domain = company.canonical_domain || company.normalized_domain || "";
                  return (
                    <tr key={company.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-semibold text-gray-900">{companyName}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-blue-600 font-mono flex items-center">
                          <Globe className="w-3.5 h-3.5 mr-1 text-gray-400" />
                          {domain}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-xs text-gray-700 bg-gray-100 px-2 py-0.5 rounded">
                          {company.industry || "General / Uncategorized"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full capitalize ${
                          company.sales_stage === 'won' ? 'bg-emerald-100 text-emerald-800' :
                          company.sales_stage === 'proposal' ? 'bg-purple-100 text-purple-800' :
                          company.sales_stage === 'contacted' ? 'bg-blue-100 text-blue-800' :
                          company.sales_stage === 'discovery' ? 'bg-amber-100 text-amber-800' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {company.sales_stage || "lead"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(company.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Link href={`/companies/${company.id}`} className="text-blue-600 hover:text-blue-900 inline-flex items-center">
                          View Intelligence <ArrowRight className="ml-1 w-4 h-4" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      {/* Pagination Controls */}
      {data && data.total > 0 && (
        <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6 rounded-lg shadow-sm border">
          <div className="flex flex-1 justify-between sm:hidden">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing <span className="font-medium">{page * pageSize + 1}</span> to{" "}
                <span className="font-medium">{Math.min((page + 1) * pageSize, data.total)}</span> of{" "}
                <span className="font-medium">{data.total}</span> records
              </p>
            </div>
            <div>
              <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                <button
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="sr-only">Previous</span>
                  <ChevronLeft className="h-5 w-5" aria-hidden="true" />
                </button>
                <span className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-700 ring-1 ring-inset ring-gray-300">
                  Page {page + 1} of {Math.max(1, totalPages)}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                  className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="sr-only">Next</span>
                  <ChevronRight className="h-5 w-5" aria-hidden="true" />
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
