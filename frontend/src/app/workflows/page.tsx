'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, Workflow, WorkflowRun, Company } from '@/lib/api';
import {
  Play,
  Pause,
  RotateCw,
  XCircle,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Layers,
  Calendar,
  Settings2,
  Trash2,
  Plus,
  Eye,
  ExternalLink,
  ShieldCheck,
  Search,
  FileSpreadsheet,
  Users
} from 'lucide-react';
import Link from 'next/link';

const STAGE_LABELS: Record<string, { label: string; desc: string }> = {
  discovery: { label: 'Prospect Discovery', desc: 'Discovers or selects target prospect companies' },
  website_analysis: { label: 'Website Analysis', desc: 'Crawls website for metadata, signals, and tech stack' },
  seo_enrichment: { label: 'SEO Enrichment', desc: 'Gathers domain metrics (DR, DA, Traffic) with cost controls' },
  ai_extraction: { label: 'AI Extraction', desc: 'Strict schema extraction of facts with evidence verification' },
  opportunity_scoring: { label: 'Opportunity Scoring', desc: 'Calculates SEO service opportunities and confidence' },
  publisher_matching: { label: 'Publisher Matching', desc: 'Matches prospect needs against real publisher inventory' },
  media_plan_generation: { label: 'Media Plan Generation', desc: 'Generates structured draft media plan with pricing' },
  human_review: { label: 'Human Review & Approval', desc: 'Pauses for user review before plan finalization' }
};

const ALL_STAGES = Object.keys(STAGE_LABELS);

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [selectedRun, setSelectedRun] = useState<WorkflowRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [companies, setCompanies] = useState<Company[]>([]);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showRunModal, setShowRunModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Form states
  const [wfName, setWfName] = useState('');
  const [wfDiscoveryQuery, setWfDiscoveryQuery] = useState('fintech');
  const [wfTargetCount, setWfTargetCount] = useState(5);
  const [wfSelectedStages, setWfSelectedStages] = useState<string[]>(ALL_STAGES);
  const [wfCron, setWfCron] = useState('');
  const [wfTimezone, setWfTimezone] = useState('UTC');
  const [wfBatchSize, setWfBatchSize] = useState(5);
  const [wfMaxRetries, setWfMaxRetries] = useState(3);
  const [wfRetryBackoff, setWfRetryBackoff] = useState(60);
  const [wfMaxRequests, setWfMaxRequests] = useState(50);
  const [wfIsEnabled, setWfIsEnabled] = useState(false);
  const [wfSelectedCompanyIds, setWfSelectedCompanyIds] = useState<string[]>([]);

  // Run modal states
  const [runTargetCompanies, setRunTargetCompanies] = useState<string[]>([]);
  const [runForce, setRunForce] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const wfList = await api.listWorkflows();
      setWorkflows(wfList);

      if (wfList.length > 0) {
        const activeWf = selectedWorkflow || wfList[0];
        setSelectedWorkflow(activeWf);
        const wfRuns = await api.listWorkflowRuns(activeWf.id);
        setRuns(wfRuns);
        if (wfRuns.length > 0 && !selectedRun) {
          setSelectedRun(wfRuns[0]);
        }
      }
    } catch (err) {
      console.error('Failed to load workflows', err);
    } finally {
      setLoading(false);
    }
  }, [selectedWorkflow, selectedRun]);

  useEffect(() => {
    loadData();
    // Fetch available companies for selection
    fetch('http://localhost:8000/companies?limit=25')
      .then((r) => r.json())
      .then((data) => setCompanies(data.items || []))
      .catch(() => {});
  }, [loadData]);

  // Polling for live status updates if a run is running
  useEffect(() => {
    const hasActiveRun = runs.some((r) => ['QUEUED', 'RUNNING'].includes(r.status));
    if (!hasActiveRun && !selectedRun) return;

    const interval = setInterval(async () => {
      if (selectedWorkflow) {
        const updatedRuns = await api.listWorkflowRuns(selectedWorkflow.id);
        setRuns(updatedRuns);
        if (selectedRun) {
          const updatedSelected = updatedRuns.find((r) => r.id === selectedRun.id);
          if (updatedSelected) setSelectedRun(updatedSelected);
        }
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [runs, selectedWorkflow, selectedRun]);

  const handleSelectWorkflow = async (wf: Workflow) => {
    setSelectedWorkflow(wf);
    setSelectedRun(null);
    try {
      const wfRuns = await api.listWorkflowRuns(wf.id);
      setRuns(wfRuns);
      if (wfRuns.length > 0) setSelectedRun(wfRuns[0]);
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleEnable = async (wf: Workflow) => {
    try {
      const updated = await api.updateWorkflow(wf.id, { is_enabled: !wf.is_enabled });
      setWorkflows((prev) => prev.map((w) => (w.id === wf.id ? updated : w)));
      if (selectedWorkflow?.id === wf.id) setSelectedWorkflow(updated);
    } catch (err) {
      alert('Failed to toggle workflow status');
    }
  };

  const handleCreateWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      const created = await api.createWorkflow({
        name: wfName,
        discovery_query: wfDiscoveryQuery || null,
        target_company_count: wfTargetCount || null,
        selected_company_ids: wfSelectedCompanyIds.length > 0 ? wfSelectedCompanyIds : null,
        enabled_stages: wfSelectedStages,
        schedule_cron: wfCron || null,
        schedule_timezone: wfTimezone,
        batch_size: wfBatchSize,
        max_retries: wfMaxRetries,
        retry_backoff_seconds: wfRetryBackoff,
        provider_request_limits: { max_requests: wfMaxRequests },
        is_enabled: wfIsEnabled
      });
      setShowCreateModal(false);
      await loadData();
      setSelectedWorkflow(created);
    } catch (err: any) {
      alert(err.message || 'Failed to create workflow');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartRun = async () => {
    if (!selectedWorkflow) return;
    setActionLoading(true);
    try {
      const run = await api.startWorkflowRun(selectedWorkflow.id, {
        trigger_type: 'manual',
        company_ids: runTargetCompanies.length > 0 ? runTargetCompanies : undefined,
        force: runForce
      });
      setShowRunModal(false);
      setRuns((prev) => [run, ...prev]);
      setSelectedRun(run);
      alert('Workflow run started!');
    } catch (err: any) {
      alert(err.message || 'Failed to start run');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelRun = async (runId: string) => {
    if (!confirm('Are you sure you want to cancel this execution?')) return;
    try {
      const cancelled = await api.cancelWorkflowRun(runId);
      setRuns((prev) => prev.map((r) => (r.id === runId ? cancelled : r)));
      if (selectedRun?.id === runId) setSelectedRun(cancelled);
    } catch (err: any) {
      alert(err.message || 'Failed to cancel run');
    }
  };

  const handleRetryRun = async (runId: string) => {
    try {
      const retried = await api.retryWorkflowRun(runId);
      setRuns((prev) => prev.map((r) => (r.id === runId ? retried : r)));
      if (selectedRun?.id === runId) setSelectedRun(retried);
      alert('Workflow execution resumed.');
    } catch (err: any) {
      alert(err.message || 'Failed to retry run');
    }
  };

  const handleApproveRun = async (runId: string) => {
    const notes = prompt('Enter approval notes (optional):', 'Approved after reviewing opportunities and media plan.');
    if (notes === null) return;
    try {
      const approved = await api.approveWorkflowRun(runId, 'human_reviewer', notes);
      setRuns((prev) => prev.map((r) => (r.id === runId ? approved : r)));
      if (selectedRun?.id === runId) setSelectedRun(approved);
      alert('Workflow approved! Media plan finalized.');
    } catch (err: any) {
      alert(err.message || 'Failed to approve run');
    }
  };

  const handleRejectRun = async (runId: string) => {
    const reason = prompt('Enter rejection reason:', 'Budget or publisher alignment issue.');
    if (!reason) return;
    try {
      const rejected = await api.rejectWorkflowRun(runId, 'human_reviewer', reason);
      setRuns((prev) => prev.map((r) => (r.id === runId ? rejected : r)));
      if (selectedRun?.id === runId) setSelectedRun(rejected);
      alert('Workflow execution rejected.');
    } catch (err: any) {
      alert(err.message || 'Failed to reject run');
    }
  };

  const handleDeleteWorkflow = async (wfId: string) => {
    if (!confirm('Are you sure you want to delete this workflow?')) return;
    try {
      await api.deleteWorkflow(wfId);
      setWorkflows((prev) => prev.filter((w) => w.id !== wfId));
      if (selectedWorkflow?.id === wfId) {
        setSelectedWorkflow(null);
        setSelectedRun(null);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to delete workflow');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"><CheckCircle2 className="w-3 h-3 mr-1" /> Completed</span>;
      case 'RUNNING':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 animate-pulse"><RotateCw className="w-3 h-3 mr-1 animate-spin" /> Running</span>;
      case 'PENDING_APPROVAL':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800"><ShieldCheck className="w-3 h-3 mr-1" /> Pending Approval</span>;
      case 'QUEUED':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800"><Clock className="w-3 h-3 mr-1" /> Queued</span>;
      case 'FAILED':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"><AlertTriangle className="w-3 h-3 mr-1" /> Failed</span>;
      case 'CANCELLED':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"><XCircle className="w-3 h-3 mr-1" /> Cancelled</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">{status}</span>;
    }
  };

  const pendingApprovalRuns = runs.filter((r) => r.status === 'PENDING_APPROVAL');

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Workflow Automation Engine</h1>
          <p className="text-gray-500 mt-1 text-sm max-w-3xl">
            Observable multi-stage pipeline orchestration: Discovery &rarr; Website Analysis &rarr; SEO Enrichment &rarr; AI Extraction &rarr; Opportunity Scoring &rarr; Publisher Matching &rarr; Media Plan &rarr; Human Review.
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => {
              setWfName('Full Prospect-to-Plan Pipeline');
              setWfSelectedStages(ALL_STAGES);
              setShowCreateModal(true);
            }}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="w-4 h-4 mr-2" /> New Workflow
          </button>
        </div>
      </div>

      {/* Metrics Summary Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-500">Configured Workflows</span>
            <Layers className="w-5 h-5 text-blue-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-gray-900">{workflows.length}</div>
        </div>
        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-500">Scheduled / Active</span>
            <Calendar className="w-5 h-5 text-green-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-gray-900">{workflows.filter((w) => w.is_enabled).length}</div>
        </div>
        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-500">Total Executions</span>
            <RotateCw className="w-5 h-5 text-purple-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-gray-900">{runs.length}</div>
        </div>
        <div className={`p-5 rounded-lg border shadow-sm ${pendingApprovalRuns.length > 0 ? 'bg-amber-50 border-amber-200' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-amber-800">Awaiting Human Review</span>
            <ShieldCheck className="w-5 h-5 text-amber-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-900">{pendingApprovalRuns.length}</div>
        </div>
      </div>

      {/* Pending Review Banner if applicable */}
      {pendingApprovalRuns.length > 0 && (
        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <ShieldCheck className="w-6 h-6 text-amber-600" />
              <div>
                <p className="text-sm font-semibold text-amber-900">
                  {pendingApprovalRuns.length} workflow run(s) are awaiting human review and approval.
                </p>
                <p className="text-xs text-amber-700">
                  Approval boundary: media plans have been generated from real publisher inventory. No external outreach or commitments occur without explicit approval.
                </p>
              </div>
            </div>
            <button
              onClick={() => setSelectedRun(pendingApprovalRuns[0])}
              className="px-3 py-1 bg-amber-600 text-white rounded text-xs font-medium hover:bg-amber-700"
            >
              Review Now
            </button>
          </div>
        </div>
      )}

      {/* Main Section: Workflow Selector & Runs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Workflows List */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <Layers className="w-5 h-5 mr-2 text-blue-600" /> Pipelines
          </h2>
          <div className="space-y-3">
            {workflows.map((wf) => {
              const isSelected = selectedWorkflow?.id === wf.id;
              return (
                <div
                  key={wf.id}
                  onClick={() => handleSelectWorkflow(wf)}
                  className={`p-4 rounded-lg border transition cursor-pointer ${
                    isSelected ? 'bg-blue-50 border-blue-400 ring-1 ring-blue-400 shadow-sm' : 'bg-white border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900 text-sm">{wf.name}</h3>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="text-xs text-gray-500">
                          {wf.enabled_stages.length} stages enabled
                        </span>
                        {wf.schedule_cron && (
                          <span className="text-xs bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded font-mono">
                            {wf.schedule_cron} ({wf.schedule_timezone || 'UTC'})
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-1" onClick={(e) => e.stopPropagation()}>
                      <button
                        title={wf.is_enabled ? 'Disable Scheduled Runs' : 'Enable Scheduled Runs'}
                        onClick={() => handleToggleEnable(wf)}
                        className={`p-1.5 rounded text-xs font-medium ${
                          wf.is_enabled ? 'text-green-700 hover:bg-green-100' : 'text-gray-400 hover:bg-gray-100'
                        }`}
                      >
                        {wf.is_enabled ? <Play className="w-4 h-4 fill-green-600 text-green-600" /> : <Pause className="w-4 h-4" />}
                      </button>
                      <button
                        title="Delete Workflow"
                        onClick={() => handleDeleteWorkflow(wf.id)}
                        className="p-1.5 text-gray-400 hover:text-red-600 rounded"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between text-xs text-gray-400 border-t border-gray-100 pt-2">
                    <span>Last run: {wf.last_run_at ? new Date(wf.last_run_at).toLocaleString() : 'Never'}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedWorkflow(wf);
                        setShowRunModal(true);
                      }}
                      className="text-blue-600 hover:text-blue-800 font-medium flex items-center"
                    >
                      <Play className="w-3 h-3 mr-1" /> Run Now
                    </button>
                  </div>
                </div>
              );
            })}

            {workflows.length === 0 && !loading && (
              <div className="p-8 text-center bg-white rounded-lg border border-dashed border-gray-300 text-gray-500 text-sm">
                No workflows created yet. Click New Workflow above to set up an automated intelligence pipeline.
              </div>
            )}
          </div>
        </div>

        {/* Right 2 Columns: Live Run Inspector & Execution History */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Run Inspector */}
          {selectedRun ? (
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 space-y-6">
              <div className="flex items-start justify-between border-b border-gray-200 pb-4">
                <div>
                  <div className="flex items-center space-x-3">
                    <h2 className="text-xl font-bold text-gray-900">Run {selectedRun.id.slice(0, 8)}</h2>
                    {getStatusBadge(selectedRun.status)}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Trigger: <span className="font-semibold uppercase">{selectedRun.trigger_type}</span> &bull; Started: {selectedRun.started_at ? new Date(selectedRun.started_at).toLocaleString() : 'N/A'}
                  </p>
                </div>
                <div className="flex space-x-2">
                  {selectedRun.status === 'PENDING_APPROVAL' && (
                    <>
                      <button
                        onClick={() => handleApproveRun(selectedRun.id)}
                        className="inline-flex items-center px-3 py-1.5 bg-green-600 text-white rounded text-xs font-medium hover:bg-green-700 shadow-sm"
                      >
                        <ShieldCheck className="w-4 h-4 mr-1" /> Approve & Finalize
                      </button>
                      <button
                        onClick={() => handleRejectRun(selectedRun.id)}
                        className="inline-flex items-center px-3 py-1.5 bg-red-100 text-red-700 rounded text-xs font-medium hover:bg-red-200"
                      >
                        <XCircle className="w-4 h-4 mr-1" /> Reject
                      </button>
                    </>
                  )}
                  {['RUNNING', 'QUEUED'].includes(selectedRun.status) && (
                    <button
                      onClick={() => handleCancelRun(selectedRun.id)}
                      className="inline-flex items-center px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-xs font-medium hover:bg-gray-200"
                    >
                      <XCircle className="w-4 h-4 mr-1" /> Cancel
                    </button>
                  )}
                  {['FAILED', 'CANCELLED', 'PARTIAL'].includes(selectedRun.status) && (
                    <button
                      onClick={() => handleRetryRun(selectedRun.id)}
                      className="inline-flex items-center px-3 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700"
                    >
                      <RotateCw className="w-4 h-4 mr-1" /> Retry Failed
                    </button>
                  )}
                </div>
              </div>

              {/* Error Summary if failed */}
              {selectedRun.error_summary && (
                <div className="bg-red-50 border-l-4 border-red-500 p-3 rounded-r text-xs text-red-800">
                  <span className="font-semibold">Error:</span> {selectedRun.error_summary}
                </div>
              )}

              {/* Visual Multi-Stage Progress Pipeline */}
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
                  Pipeline Progression (8-Stage Strict Ordering)
                </h3>
                <div className="space-y-3">
                  {selectedWorkflow?.enabled_stages.map((stgKey, idx) => {
                    const stgInfo = STAGE_LABELS[stgKey] || { label: stgKey, desc: '' };
                    const progress = selectedRun.stage_progress?.[stgKey];
                    const stageStatus = progress?.status || (selectedRun.current_stage === stgKey ? 'RUNNING' : 'PENDING');
                    const isCurrent = selectedRun.current_stage === stgKey;

                    return (
                      <div
                        key={stgKey}
                        className={`p-3 rounded-md border flex items-center justify-between text-sm ${
                          stageStatus === 'COMPLETED'
                            ? 'bg-green-50 border-green-200'
                            : stageStatus === 'AWAITING_REVIEW'
                            ? 'bg-amber-50 border-amber-300 ring-1 ring-amber-300'
                            : isCurrent
                            ? 'bg-blue-50 border-blue-300'
                            : stageStatus === 'FAILED'
                            ? 'bg-red-50 border-red-200'
                            : 'bg-gray-50 border-gray-200 text-gray-400'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <span className="w-6 h-6 flex items-center justify-center rounded-full bg-white border border-gray-300 font-bold text-xs text-gray-700">
                            {idx + 1}
                          </span>
                          <div>
                            <div className="font-semibold text-gray-900 flex items-center space-x-2">
                              <span>{stgInfo.label}</span>
                              {isCurrent && <span className="text-[10px] bg-blue-600 text-white px-1.5 py-0.2 rounded font-normal uppercase">Current</span>}
                            </div>
                            <div className="text-xs text-gray-500">{stgInfo.desc}</div>
                            {progress?.error_message && (
                              <div className="text-xs text-red-600 mt-1">{progress.error_message}</div>
                            )}
                          </div>
                        </div>

                        <div className="text-right text-xs">
                          <div>{getStatusBadge(stageStatus)}</div>
                          {progress?.completed_at && (
                            <div className="text-[11px] text-gray-400 mt-1">
                              {new Date(progress.completed_at).toLocaleTimeString()}
                            </div>
                          )}
                          {progress?.total_items !== undefined && (
                            <div className="text-[11px] text-gray-500 mt-0.5">
                              {progress.successful_items || 0}/{progress.total_items} items
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Target Prospects in Run */}
              {selectedRun.parameters?.company_ids && selectedRun.parameters.company_ids.length > 0 && (
                <div className="border-t border-gray-100 pt-4">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Target Prospects ({selectedRun.parameters.company_ids.length})</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedRun.parameters.company_ids.map((cid: string) => (
                      <Link
                        key={cid}
                        href={`/companies/${cid}`}
                        target="_blank"
                        className="inline-flex items-center px-2.5 py-1 bg-gray-100 hover:bg-gray-200 text-gray-800 text-xs rounded border border-gray-200"
                      >
                        <ExternalLink className="w-3 h-3 mr-1 text-gray-500" /> View Prospect
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-8 text-center text-gray-500 text-sm">
              Select an execution below or start a new run to inspect live stage progression.
            </div>
          )}

          {/* Execution History Table */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
              <h3 className="font-semibold text-gray-900 text-sm">Execution History</h3>
              <span className="text-xs text-gray-500">{runs.length} runs recorded</span>
            </div>
            <div className="divide-y divide-gray-200">
              {runs.map((r) => (
                <div
                  key={r.id}
                  onClick={() => setSelectedRun(r)}
                  className={`p-4 hover:bg-gray-50 cursor-pointer flex items-center justify-between transition ${
                    selectedRun?.id === r.id ? 'bg-blue-50/50' : ''
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold text-gray-900">{r.id.slice(0, 8)}</span>
                      {getStatusBadge(r.status)}
                      <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded uppercase font-medium">{r.trigger_type}</span>
                    </div>
                    <div className="text-xs text-gray-500">
                      Started: {r.started_at ? new Date(r.started_at).toLocaleString() : 'N/A'} &bull; Stage: <span className="font-medium text-gray-700">{r.current_stage || 'Done'}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedRun(r);
                      }}
                      className="px-2.5 py-1 text-xs border border-gray-300 rounded hover:bg-white text-gray-700 font-medium"
                    >
                      Inspect
                    </button>
                  </div>
                </div>
              ))}
              {runs.length === 0 && (
                <div className="p-6 text-center text-gray-500 text-sm">
                  No executions recorded for this workflow yet. Click Run Now to start one.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Modal: Create Workflow */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto space-y-6">
            <div className="flex justify-between items-center border-b pb-3">
              <h2 className="text-lg font-bold text-gray-900">Create Workflow Automation</h2>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-gray-600">&times;</button>
            </div>

            <form onSubmit={handleCreateWorkflow} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase">Workflow Name</label>
                <input
                  type="text"
                  required
                  value={wfName}
                  onChange={(e) => setWfName(e.target.value)}
                  placeholder="e.g. Enterprise SEO Discovery to Plan"
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm"
                />
              </div>

              {/* Stages Selection */}
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-2">Enabled Stages (Ordered Execution)</label>
                <div className="space-y-2 border border-gray-200 rounded-md p-3 max-h-48 overflow-y-auto">
                  {ALL_STAGES.map((sKey) => {
                    const isChecked = wfSelectedStages.includes(sKey);
                    return (
                      <label key={sKey} className="flex items-center space-x-2 text-sm cursor-pointer">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setWfSelectedStages([...wfSelectedStages, sKey]);
                            } else {
                              setWfSelectedStages(wfSelectedStages.filter((s) => s !== sKey));
                            }
                          }}
                          className="rounded text-blue-600"
                        />
                        <span className="font-medium text-gray-800">{STAGE_LABELS[sKey]?.label}</span>
                        <span className="text-xs text-gray-400">({STAGE_LABELS[sKey]?.desc})</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Discovery vs Selection */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase">Discovery Query</label>
                  <input
                    type="text"
                    value={wfDiscoveryQuery}
                    onChange={(e) => setWfDiscoveryQuery(e.target.value)}
                    placeholder="e.g. fintech, b2b saas"
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase">Target Count / Limit</label>
                  <input
                    type="number"
                    value={wfTargetCount}
                    onChange={(e) => setWfTargetCount(parseInt(e.target.value) || 5)}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>

              {/* Scheduling */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase">Schedule Cron (Optional)</label>
                  <input
                    type="text"
                    value={wfCron}
                    onChange={(e) => setWfCron(e.target.value)}
                    placeholder="e.g. 0 9 * * 1 (Weekly Mon 9am)"
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase">Timezone</label>
                  <select
                    value={wfTimezone}
                    onChange={(e) => setWfTimezone(e.target.value)}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  >
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">America/New_York (EST)</option>
                    <option value="Europe/London">Europe/London (GMT)</option>
                    <option value="Asia/Karachi">Asia/Karachi (PKT)</option>
                  </select>
                </div>
              </div>

              {/* Reliability & Limits */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase">Max Retries</label>
                  <input
                    type="number"
                    value={wfMaxRetries}
                    onChange={(e) => setWfMaxRetries(parseInt(e.target.value) || 3)}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase">Backoff (Sec)</label>
                  <input
                    type="number"
                    value={wfRetryBackoff}
                    onChange={(e) => setWfRetryBackoff(parseInt(e.target.value) || 60)}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase">Provider Req Limit</label>
                  <input
                    type="number"
                    value={wfMaxRequests}
                    onChange={(e) => setWfMaxRequests(parseInt(e.target.value) || 50)}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="enableWf"
                  checked={wfIsEnabled}
                  onChange={(e) => setWfIsEnabled(e.target.checked)}
                  className="rounded text-blue-600"
                />
                <label htmlFor="enableWf" className="text-sm font-medium text-gray-800">
                  Enable Scheduled Execution
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border rounded-md text-sm text-gray-600 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium shadow-sm"
                >
                  {actionLoading ? 'Creating...' : 'Create Workflow'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Start Run with Prospect Selection */}
      {showRunModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex justify-between items-center border-b pb-3">
              <h2 className="text-lg font-bold text-gray-900">Start Workflow Execution</h2>
              <button onClick={() => setShowRunModal(false)} className="text-gray-400 hover:text-gray-600">&times;</button>
            </div>

            <p className="text-sm text-gray-500">
              Run <span className="font-semibold text-gray-800">{selectedWorkflow?.name}</span> manually. You can target existing prospects or use the workflow&apos;s discovery configuration.
            </p>

            {companies.length > 0 && (
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Target Specific Prospects (Optional)
                </label>
                <div className="border border-gray-200 rounded max-h-40 overflow-y-auto p-2 space-y-1">
                  {companies.slice(0, 15).map((co) => (
                    <label key={co.id} className="flex items-center space-x-2 text-xs cursor-pointer hover:bg-gray-50 p-1 rounded">
                      <input
                        type="checkbox"
                        checked={runTargetCompanies.includes(co.id)}
                        onChange={(e) => {
                          if (e.target.checked) setRunTargetCompanies([...runTargetCompanies, co.id]);
                          else setRunTargetCompanies(runTargetCompanies.filter((c) => c !== co.id));
                        }}
                        className="rounded text-blue-600"
                      />
                      <span className="font-medium text-gray-800">{co.name}</span>
                      <span className="text-gray-400">({co.normalized_domain})</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="forceRun"
                checked={runForce}
                onChange={(e) => setRunForce(e.target.checked)}
                className="rounded text-blue-600"
              />
              <label htmlFor="forceRun" className="text-xs font-medium text-gray-700">
                Force Execution (bypass active duplicate run checks)
              </label>
            </div>

            <div className="flex justify-end space-x-3 pt-4 border-t">
              <button
                type="button"
                onClick={() => setShowRunModal(false)}
                className="px-4 py-2 border rounded-md text-sm text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleStartRun}
                disabled={actionLoading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium shadow-sm"
              >
                {actionLoading ? 'Starting...' : 'Start Run'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
