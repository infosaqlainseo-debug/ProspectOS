"use client";

import { useApi, api } from "@/lib/api";
import { Loader2, Plus, Trash2, Download, Printer, FileText, AlertTriangle } from "lucide-react";
import { useState, useEffect } from "react";

export function MediaPlanSection({ companyId }: { companyId: string }) {
  const { data: plans, mutate: mutatePlans } = useApi<any[]>(`/media-plans/company/${companyId}`);
  const [activePlanId, setActivePlanId] = useState<string | null>(null);
  
  useEffect(() => {
    if (plans && plans.length > 0 && !activePlanId) {
      setActivePlanId(plans[0].id);
    }
  }, [plans, activePlanId]);
  
  // Try to find an existing plan (for now we assume 1 plan per prospect, or we could list them)
  // Since we don't have a list endpoint, we will just keep track of it in local state or create a new one.
  // Actually, we could add a list endpoint, but let's just create a new one if requested.
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
      <div className="flex justify-between items-center border-b pb-2">
        <div className="flex items-center text-lg font-semibold">
          <FileText className="w-5 h-5 mr-2 text-gray-500" /> Media Plan Builder
        </div>
        {!activePlanId && (
          <button 
            onClick={async () => {
              try {
                const plan = await api.createMediaPlan(companyId);
                setActivePlanId(plan.id);
                mutatePlans();
              } catch(err) {
                console.error(err);
                alert("Failed to create Media Plan.");
              }
            }}
            className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded hover:bg-blue-700"
          >
            Create New Plan
          </button>
        )}
      </div>

      {activePlanId ? (
        <MediaPlanEditor planId={activePlanId} />
      ) : (
        <div className="text-sm text-gray-500 py-4 text-center">
          No active media plan. Create one to begin organizing publishers for export.
        </div>
      )}
    </div>
  );
}

function MediaPlanEditor({ planId }: { planId: string }) {
  const { data: plan, isLoading, error, mutate } = useApi<any>(`/media-plans/${planId}`);

  if (isLoading) return <div className="py-4"><Loader2 className="w-5 h-5 animate-spin text-gray-500 mx-auto" /></div>;
  if (error || !plan) return <div className="text-red-500 py-4">Failed to load media plan.</div>;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="font-semibold text-lg text-gray-900">{plan.name}</h3>
          <span className="text-xs text-gray-500">Status: {plan.status}</span>
        </div>
        <div className="flex space-x-2 print:hidden">
          <a 
            href={api.exportMediaPlanUrl(planId)} 
            className="inline-flex items-center text-sm border border-gray-300 px-3 py-1.5 rounded hover:bg-gray-50 text-gray-700"
          >
            <Download className="w-4 h-4 mr-2" /> Excel
          </a>
          <button 
            onClick={handlePrint}
            className="inline-flex items-center text-sm border border-gray-300 px-3 py-1.5 rounded hover:bg-gray-50 text-gray-700"
          >
            <Printer className="w-4 h-4 mr-2" /> PDF / Print
          </button>
        </div>
      </div>

      {!plan.can_calculate_totals && plan.calculation_warning && (
        <div className="bg-orange-50 border border-orange-200 p-3 rounded flex items-start print:hidden">
          <AlertTriangle className="w-5 h-5 text-orange-500 mr-2 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-orange-800">{plan.calculation_warning}</p>
        </div>
      )}

      {plan.items && plan.items.length > 0 ? (
        <div className="overflow-x-auto border border-gray-200 rounded-lg">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr className="text-left text-gray-500 border-b">
                <th className="px-4 py-3 font-medium">Publisher</th>
                <th className="px-4 py-3 font-medium">Domain</th>
                <th className="px-4 py-3 font-medium">Metrics (DA/Traffic)</th>
                <th className="px-4 py-3 font-medium">Price</th>
                <th className="px-4 py-3 font-medium print:hidden">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {plan.items.map((item: any) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {item.publisher_name || 'Unknown'}
                    {item.verification_status !== 'VERIFIED' && (
                      <span className="ml-2 text-[10px] bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded">
                        Unverified
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500">{item.canonical_domain}</td>
                  <td className="px-4 py-3 text-gray-500">
                    DA: {item.metric_da || '-'}{' | '}
                    Traffic: {item.metric_traffic ? item.metric_traffic.toLocaleString() : '-'}
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {item.proposed_price ? `${item.proposed_price} ${item.proposed_currency || ''}` : <span className="text-orange-500 text-xs">Missing</span>}
                  </td>
                  <td className="px-4 py-3 print:hidden">
                    <button 
                      onClick={async () => {
                        try {
                          await api.removePublisherFromPlan(planId, item.id);
                          mutate();
                        } catch(err) {
                          alert("Failed to remove publisher.");
                        }
                      }}
                      className="text-red-500 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50 font-semibold border-t">
              <tr>
                <td colSpan={3} className="px-4 py-3 text-right text-gray-700">Total:</td>
                <td className="px-4 py-3 text-gray-900">
                  {plan.can_calculate_totals ? `${plan.total_price} ${plan.currency || ''}` : 'N/A'}
                </td>
                <td className="print:hidden"></td>
              </tr>
            </tfoot>
          </table>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500 border border-dashed rounded-lg">
          No publishers added yet. You can add them from the Matching Results.
        </div>
      )}
    </div>
  );
}
