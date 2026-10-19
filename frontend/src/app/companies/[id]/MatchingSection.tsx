"use client";

import { useState } from "react";
import { Loader2, Target, CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";

export function MatchingSection({ companyId }: { companyId: string }) {
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<any>(null);
  const [run, setRun] = useState<any>(null);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const { api } = await import('@/lib/api');
      
      // Auto-populate profile using AI data if it doesn't exist
      let prof;
      try {
        prof = await api.getCampaignProfile(companyId);
      } catch (err) {
        // Just create a default one
        prof = await api.updateCampaignProfile(companyId, {
          target_industry: "Technology", // Usually drawn from AI Extracted attribute
          max_budget: 200,
          budget_currency: "USD"
        });
      }
      setProfile(prof);
    } catch(err: any) {
      setError(err.message || "Failed to fetch profile");
    } finally {
      setLoading(false);
    }
  };

  const handleMatch = async () => {
    setLoading(true);
    setError(null);
    try {
      const { api } = await import('@/lib/api');
      // Save profile updates before running
      await api.updateCampaignProfile(companyId, profile);
      
      // Run Match
      const r = await api.runMatching(companyId);
      setRun(r);
      
      // Fetch Results
      const res = await api.getMatchingResults(r.id);
      setResults(res);
    } catch(err: any) {
      setError(err.message || "Failed to run matching");
    } finally {
      setLoading(false);
    }
  };

  if (!profile) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-6">
        <div className="flex justify-between items-center">
          <div className="flex items-center text-lg font-semibold border-b border-gray-100 pb-2 flex-grow">
            <Target className="w-5 h-5 mr-2 text-indigo-500" /> Phase 2.1 Media Planning & Matching
          </div>
        </div>
        <div className="mt-4">
          <button onClick={fetchProfile} disabled={loading} className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50">
            {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : "Initialize Prospect Profile"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-6 space-y-6">
      <div className="flex items-center text-lg font-semibold border-b border-gray-100 pb-2">
        <Target className="w-5 h-5 mr-2 text-indigo-500" /> Media Planning & Matching Profile
      </div>
      
      {error && <div className="p-4 bg-red-50 text-red-700 rounded-md text-sm">{error}</div>}
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Target Industry</label>
          <input type="text" value={profile.target_industry || ""} onChange={(e) => setProfile({...profile, target_industry: e.target.value})} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm border py-2 px-3 sm:text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Target Geography</label>
          <input type="text" value={profile.target_geography || ""} onChange={(e) => setProfile({...profile, target_geography: e.target.value})} placeholder="e.g. United States" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm border py-2 px-3 sm:text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Max Budget (Strict Constraint)</label>
          <input type="number" value={profile.max_budget || ""} onChange={(e) => setProfile({...profile, max_budget: parseFloat(e.target.value) || 0})} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm border py-2 px-3 sm:text-sm" />
        </div>
      </div>

      <div className="pt-4 flex items-center justify-between border-t border-gray-100">
         <span className="text-sm text-gray-500 italic">Matching engine scores against the real inventory dataset.</span>
         <button onClick={handleMatch} disabled={loading} className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50">
            {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : "Run Publisher Matching"}
         </button>
      </div>

      {run && (
        <div className="mt-6 space-y-4">
           <div className="flex justify-between items-center p-4 bg-indigo-50 rounded-md border border-indigo-100 text-sm">
             <div><span className="font-semibold text-indigo-900">Run Status:</span> {run.status}</div>
             <div><span className="font-semibold text-indigo-900">Eligible Publishers:</span> {run.total_eligible}</div>
             <div><span className="font-semibold text-indigo-900">Excluded (Constraints):</span> {run.total_excluded}</div>
           </div>
           
           <div className="space-y-4">
              <h3 className="font-semibold text-gray-900 border-b pb-2">Top Recommended Publishers (Ranked)</h3>
              {results.length === 0 ? (
                 <div className="text-sm text-gray-500">No publishers met the criteria.</div>
              ) : (
                 results.slice(0, 10).map((res, i) => (
                    <div key={res.id} className="p-4 border rounded-md shadow-sm">
                       <div className="flex justify-between items-start">
                         <div>
                            <div className="font-bold text-lg text-indigo-700 flex items-center">
                              #{res.rank} — Publisher ID: {res.publisher_id.slice(0, 8)}
                              {res.overall_score > 40 && <ShieldCheck className="w-4 h-4 text-green-500 ml-2 inline" />}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">Overall Match Score: {res.overall_score.toFixed(1)} / 100</div>
                         </div>
                         <button 
                           onClick={async () => {
                             try {
                               const { api } = await import('@/lib/api');
                               const plans = await api.getCompanyMediaPlans(companyId);
                               let planId;
                               if (plans.length > 0) {
                                 planId = plans[0].id;
                               } else {
                                 const newPlan = await api.createMediaPlan(companyId);
                                 planId = newPlan.id;
                               }
                               await api.addPublisherToPlan(planId, res.publisher_id, res.id);
                               alert("Added to Media Plan successfully!");
                             } catch(err) {
                               alert("Failed to add to Media Plan. It might already be in the plan.");
                             }
                           }}
                           className="text-sm font-medium text-indigo-600 hover:underline border border-indigo-200 px-3 py-1 rounded"
                         >
                           Add to Media Plan
                         </button>
                       </div>
                       
                       <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 mt-4 text-xs font-mono bg-gray-50 p-2 rounded">
                         <div>Topical: {res.component_scores.topical_relevance.toFixed(1)}</div>
                         <div>Quality: {res.component_scores.publisher_quality.toFixed(1)}</div>
                         <div>Price: {res.component_scores.price_fit.toFixed(1)}</div>
                         <div>Geo: {res.component_scores.geographic_relevance.toFixed(1)}</div>
                       </div>
                       
                       <div className="mt-3 text-sm">
                         <div className="font-medium text-gray-700 mb-1">Evidence & Reasons:</div>
                         <ul className="list-disc pl-5 space-y-1 text-gray-600">
                            {res.reasons.map((r: any, idx: number) => (
                               <li key={idx}>[{r.factor}] {r.evidence}</li>
                            ))}
                         </ul>
                       </div>
                       
                       {res.warnings && res.warnings.length > 0 && (
                          <div className="mt-3 text-sm">
                             <div className="font-medium text-orange-700 mb-1 flex items-center">
                               <AlertTriangle className="w-4 h-4 mr-1 inline" /> Warnings:
                             </div>
                             <ul className="list-disc pl-5 space-y-1 text-orange-600">
                                {res.warnings.map((w: string, idx: number) => (
                                   <li key={idx}>{w}</li>
                                ))}
                             </ul>
                          </div>
                       )}
                    </div>
                 ))
              )}
           </div>
        </div>
      )}
    </div>
  );
}
