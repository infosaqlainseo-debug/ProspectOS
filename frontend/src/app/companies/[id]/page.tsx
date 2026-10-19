"use client";

import { useApi, Company, Evidence, ProviderObservation, AIObservation, AIContradiction, WebsiteAnalysisResult, OpportunityProfile } from "@/lib/api";
import { useParams } from "next/navigation";
import { Loader2, Globe, FileCheck2, Bot, Activity, AlertTriangle, Target } from "lucide-react";
import { useState, Suspense } from "react";
import { MatchingSection } from "./MatchingSection";
import { MediaPlanSection } from "./MediaPlanSection";

export default function CompanyDetailPage() {
  return (
    <Suspense fallback={<div className="flex justify-center mt-32"><Loader2 className="w-8 h-8 animate-spin text-blue-500" /></div>}>
      <CompanyDetailContent />
    </Suspense>
  );
}

function CompanyDetailContent() {
  const params = useParams();
  const id = params.id as string;

  const { data: company, isLoading: loadingCompany } = useApi<Company>(`/companies/${id}`);
  // evidenceData can be utilized when evidence UI is built
  const { data: websiteData } = useApi<WebsiteAnalysisResult>(`/analysis/website/${id}`);
  const { data: seoData } = useApi<{observations: ProviderObservation[]}>(`/enrichment/seo/${id}`);
  const { data: aiData } = useApi<{observations: AIObservation[]}>(`/ai/extraction/${id}/history`);
  const { data: contradictionsData } = useApi<{contradictions: AIContradiction[]}>(`/ai/extraction/${id}/contradictions`);
  const { data: opportunityData } = useApi<OpportunityProfile[]>(`/opportunity/${id}`);
  
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handleAction = async (actionType: 'analyze' | 'seo' | 'ai' | 'opportunity') => {
    setActionLoading(actionType);
    try {
      const { api } = await import('@/lib/api');
      if (actionType === 'analyze') {
        await api.triggerAnalysis([id]);
        alert("Website analysis job enqueued!");
      } else if (actionType === 'seo') {
        await api.triggerEnrichment([id]);
        alert("SEO enrichment job enqueued!");
      } else if (actionType === 'ai') {
        await api.triggerAIExtraction([id]);
        alert("AI structured extraction job enqueued!");
      } else if (actionType === 'opportunity') {
        await api.triggerOpportunityEvaluation(id);
        alert("Opportunity evaluation job enqueued!");
      }
    } catch(err: any) {
      console.error(err);
      alert(`Action failed: ${err.message || "Unknown error"}`);
    } finally {
      setActionLoading(null);
    }
  };

  if (loadingCompany) {
    return <div className="flex justify-center mt-32"><Loader2 className="w-8 h-8 animate-spin text-blue-500" /></div>;
  }
  
  if (!company) {
    return <div className="text-center mt-32 text-red-500">Company not found or backend unavailable.</div>;
  }

  const companyName = company.company_name || company.name || "Unnamed Company";
  const domain = company.canonical_domain || company.normalized_domain || "";
  const isAccessRestricted = websiteData?.status === "ACCESS_RESTRICTED" || websiteData?.http_status === 403;
  const latestOpportunity = opportunityData?.[0];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-start bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{companyName}</h1>
          {domain && (
            <a href={`https://${domain}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline flex items-center mt-1">
              <Globe className="w-4 h-4 mr-1" /> {domain}
            </a>
          )}
          <p className="text-xs text-gray-400 mt-2">Discovered: {new Date(company.created_at).toLocaleString()}</p>
        </div>
        
        <div className="flex flex-wrap gap-2">
          <ActionButton 
            label={actionLoading === 'opportunity' ? "Queuing..." : "Evaluate Opportunity"} 
            icon={<Target className="w-4 h-4 mr-2" />} 
            onClick={() => handleAction('opportunity')} 
            disabled={actionLoading !== null}
          />
          <ActionButton 
            label={actionLoading === 'analyze' ? "Queuing..." : "Analyze Website"} 
            icon={<Globe className="w-4 h-4 mr-2" />} 
            onClick={() => handleAction('analyze')} 
            disabled={actionLoading !== null}
          />
          <ActionButton 
            label={actionLoading === 'seo' ? "Queuing..." : "SEO Enrichment"} 
            icon={<Activity className="w-4 h-4 mr-2" />} 
            onClick={() => handleAction('seo')} 
            disabled={actionLoading !== null}
          />
          <ActionButton 
            label={actionLoading === 'ai' ? "Queuing..." : "AI Extraction"} 
            icon={<Bot className="w-4 h-4 mr-2" />} 
            onClick={() => handleAction('ai')} 
            disabled={actionLoading !== null}
          />
        </div>
      </div>

      {/* Access Restricted / Cloudflare 403 Honest Banner */}
      {isAccessRestricted && (
        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg shadow-sm">
          <div className="flex items-start">
            <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 mr-3 flex-shrink-0" />
            <div className="space-y-1">
              <h4 className="text-sm font-semibold text-amber-900">
                Target Domain Access Restricted (HTTP 403 / Cloudflare WAF Challenge)
              </h4>
              <p className="text-sm text-amber-800">
                This domain enforces edge bot protection. In accordance with ProspectOS ethical crawling rules and non-fabrication guarantees, the crawler recorded the 403 status, avoided aggressive retry loops, and marked on-page attributes as UNVERIFIED. Downstream scoring transparently factors in missing crawl data without generating synthetic defect claims.
              </p>
              {websiteData?.error_message && (
                <div className="text-xs font-mono text-amber-900 bg-amber-100/70 px-2 py-1 rounded inline-block">
                  Diagnostic: {websiteData.error_message}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {latestOpportunity && (
        <div className="bg-blue-50 p-6 rounded-lg shadow-sm border border-blue-200 space-y-4">
          <div className="flex items-center text-lg font-semibold text-blue-900 border-b border-blue-100 pb-2">
            <Target className="w-5 h-5 mr-2 text-blue-600" /> Opportunity Intelligence: {latestOpportunity.recommended_service}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="text-sm font-medium text-blue-800 mb-2">Score & Confidence</div>
              <div className="flex items-end space-x-4 mb-4">
                <div className="text-4xl font-bold text-blue-700">{latestOpportunity.opportunity_score.toFixed(0)}</div>
                <div className="text-sm text-blue-600 pb-1">Confidence: {(latestOpportunity.confidence_level * 100).toFixed(0)}%</div>
              </div>
              <DataRow label="Data Freshness" value={latestOpportunity.data_freshness} />
              <DataRow label="Next Action" value={latestOpportunity.recommended_next_action || "None"} />
            </div>
            <div>
              {latestOpportunity.identified_problems && latestOpportunity.identified_problems.length > 0 && (
                <>
                  <div className="text-sm font-medium text-blue-800 mb-2">Identified Gaps</div>
                  <ul className="list-disc pl-5 text-sm text-blue-900 space-y-1">
                    {latestOpportunity.identified_problems.map((p, i) => <li key={i}>{p}</li>)}
                  </ul>
                </>
              )}
              {latestOpportunity.missing_information && latestOpportunity.missing_information.length > 0 && (
                <>
                  <div className="text-sm font-medium text-orange-800 mt-4 mb-2">Missing Data</div>
                  <ul className="list-disc pl-5 text-sm text-orange-900 space-y-1">
                    {latestOpportunity.missing_information.map((m, i) => <li key={i}>{m}</li>)}
                  </ul>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* MATCHING SECTION */}
      <MatchingSection companyId={id} />

      {/* MEDIA PLAN BUILDER */}
      <MediaPlanSection companyId={id} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Website Intelligence */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
          <div className="flex items-center text-lg font-semibold border-b pb-2">
            <FileCheck2 className="w-5 h-5 mr-2 text-gray-500" /> Website Intelligence
          </div>
          {websiteData?.status === "NO_SCAN_FOUND" ? (
             <div className="text-sm text-gray-500 italic py-4">Not available.</div>
          ) : websiteData ? (
             <div className="space-y-3">
               <DataRow label="HTTP Status" value={websiteData.http_status} />
               <DataRow label="Title" value={websiteData.title || "Not available"} />
               <DataRow label="Scan Status" value={websiteData.status} />
               <DataRow label="Last Scanned" value={websiteData.scanned_at ? new Date(websiteData.scanned_at).toLocaleString() : "N/A"} />
             </div>
          ) : (
             <div className="text-sm text-gray-500 italic py-4">Loading...</div>
          )}
        </div>

        {/* SEO Intelligence */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
          <div className="flex items-center text-lg font-semibold border-b pb-2">
            <Activity className="w-5 h-5 mr-2 text-gray-500" /> SEO Intelligence
          </div>
          {seoData?.observations && seoData.observations.length > 0 ? (
             <div className="space-y-3">
               {seoData.observations.map(obs => (
                 <div key={obs.id} className="flex justify-between items-center text-sm border-b pb-2 last:border-0">
                    <div>
                      <span className="font-medium">{obs.metric_name}</span>
                      <span className="text-xs text-gray-400 ml-2 bg-gray-100 px-1 py-0.5 rounded">{obs.provider}</span>
                    </div>
                    <div className="font-mono text-gray-900">{obs.metric_value}</div>
                 </div>
               ))}
             </div>
          ) : (
             <div className="text-sm text-gray-500 italic py-4">Not available.</div>
          )}
        </div>
        
        {/* AI Intelligence */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4 lg:col-span-2">
          <div className="flex justify-between items-center border-b pb-2">
            <div className="flex items-center text-lg font-semibold">
              <Bot className="w-5 h-5 mr-2 text-gray-500" /> AI Intelligence (Extracted Attributes)
            </div>
            <ManualOverrideModal companyId={id} />
          </div>
          {aiData?.observations && aiData.observations.length > 0 ? (
             <div className="overflow-x-auto">
               <table className="min-w-full text-sm">
                 <thead>
                   <tr className="text-left text-gray-500 border-b">
                     <th className="pb-2 font-medium">Attribute</th>
                     <th className="pb-2 font-medium">Value</th>
                     <th className="pb-2 font-medium">Status</th>
                     <th className="pb-2 font-medium">Confidence</th>
                     <th className="pb-2 font-medium">Evidence</th>
                   </tr>
                 </thead>
                 <tbody>
                   {aiData.observations.map(obs => (
                     <tr key={obs.id} className="border-b last:border-0">
                       <td className="py-3 font-medium text-gray-900">{obs.attribute_name}</td>
                       <td className="py-3">{obs.attribute_value}</td>
                       <td className="py-3">
                         <span className={`px-2 py-0.5 rounded text-xs ${obs.verification_status === 'VERIFIED' ? 'bg-green-100 text-green-800' : obs.verification_status === 'CONTRADICTED' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'}`}>
                           {obs.verification_status}
                         </span>
                       </td>
                       <td className="py-3 font-mono text-xs text-gray-500">{(obs.confidence ? (obs.confidence * 100).toFixed(0) + '%' : 'N/A')}</td>
                       <td className="py-3 text-xs text-gray-500 italic line-clamp-2 max-w-xs" title={obs.evidence_text || ""}>
                         &quot;{obs.evidence_text}&quot;
                       </td>
                     </tr>
                   ))}
                 </tbody>
               </table>
             </div>
          ) : (
             <div className="text-sm text-gray-500 italic py-4">Not available.</div>
          )}
        </div>

        {/* AI Contradictions */}
        {contradictionsData?.contradictions && contradictionsData.contradictions.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow-sm border border-red-200 space-y-4 lg:col-span-2">
            <div className="flex items-center text-lg font-semibold text-red-800 border-b border-red-100 pb-2">
              <AlertTriangle className="w-5 h-5 mr-2 text-red-600" /> AI Contradictions Detected
            </div>
            <div className="space-y-4">
              {contradictionsData.contradictions.map(c => (
                <div key={c.id} className="p-4 bg-red-50 rounded border border-red-100 text-sm">
                  <div className="font-medium text-red-900 mb-2">Attribute: {c.attribute_name}</div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="font-medium text-red-800">Existing Value:</span> {c.existing_value || "None"}
                    </div>
                    <div>
                      <span className="font-medium text-red-800">New Value:</span> {c.new_value || "None"}
                    </div>
                  </div>
                  <div className="mt-3 flex justify-end">
                    <button className="text-xs font-medium text-blue-600 hover:underline">
                      Review & Resolve
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function DataRow({ label, value }: { label: string, value: string | number | null | undefined }) {
  return (
    <div className="flex justify-between items-center text-sm border-b border-gray-100 pb-2 last:border-0">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-900">{value}</span>
    </div>
  );
}

function ActionButton({ label, icon, onClick, disabled }: { label: string, icon: React.ReactNode, onClick: () => void, disabled?: boolean }) {
  return (
    <button 
      onClick={onClick} 
      disabled={disabled}
      className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {icon} {label}
    </button>
  );
}

function ManualOverrideModal({ companyId }: { companyId: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const [attribute, setAttribute] = useState("");
  const [value, setValue] = useState("");
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const { api } = await import('@/lib/api');
      await api.submitManualOverride(companyId, attribute, value, reason);
      setIsOpen(false);
      window.location.reload(); // Quick refresh to show new data
    } catch (err) {
      console.error(err);
      alert("Failed to submit override.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        className="text-xs bg-white border border-gray-300 text-gray-700 px-3 py-1.5 rounded hover:bg-gray-50"
      >
        Manual Override
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Add Manual Observation</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Attribute</label>
                <input required value={attribute} onChange={e => setAttribute(e.target.value)} type="text" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm border py-2 px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm" placeholder="e.g. business_model" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Value</label>
                <input required value={value} onChange={e => setValue(e.target.value)} type="text" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm border py-2 px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm" placeholder="e.g. SaaS" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Reason</label>
                <input required value={reason} onChange={e => setReason(e.target.value)} type="text" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm border py-2 px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm" placeholder="e.g. Verified by sales team" />
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button type="button" onClick={() => setIsOpen(false)} className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50">
                  Cancel
                </button>
                <button type="submit" disabled={isSubmitting} className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50">
                  {isSubmitting ? "Saving..." : "Save Override"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
