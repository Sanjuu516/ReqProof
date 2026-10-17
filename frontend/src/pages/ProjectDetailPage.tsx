import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Project, Requirement, Artifact, AnalysisRun, ClaimResult, RequirementGraph } from '../types';
import { Navbar } from '../components/Navbar';
import { StatusBadge } from '../components/StatusBadge';
import { EvidenceModal } from '../components/EvidenceModal';
import { RequirementGraphView } from '../components/RequirementGraph';
import {
  Upload, Play, FileText, Layers, GitFork, AlertTriangle, CheckCircle,
  FileCode, ArrowLeft, RefreshCw, Plus, Sparkles, Filter, FolderPlus,
  Zap, Check, HelpCircle, ArrowRight
} from 'lucide-react';

export const ProjectDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const projectId = parseInt(id || '0', 10);
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'requirements' | 'artifacts' | 'graph' | 'reports'>('dashboard');
  const [loading, setLoading] = useState(true);

  // Data states
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [latestRun, setLatestRun] = useState<AnalysisRun | null>(null);
  const [results, setResults] = useState<ClaimResult[]>([]);
  const [graph, setGraph] = useState<RequirementGraph | null>(null);

  // UI interaction states
  const [analyzing, setAnalyzing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [newReqText, setNewReqText] = useState('');
  const [addingReq, setAddingReq] = useState(false);
  const [selectedResult, setSelectedResult] = useState<ClaimResult | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const loadAllData = async () => {
    if (!projectId) return;
    try {
      setLoading(true);
      const [projData, reqsData, artsData, historyData, graphData] = await Promise.all([
        api.getProject(projectId),
        api.listRequirements(projectId),
        api.listArtifacts(projectId),
        api.getProjectHistory(projectId),
        api.getRequirementGraph(projectId).catch(() => null),
      ]);

      setProject(projData);
      setRequirements(reqsData);
      setArtifacts(artsData);
      setGraph(graphData);

      if (historyData.length > 0) {
        const run = historyData[0];
        setLatestRun(run);
        const resData = await api.getAnalysisResults(run.analysis_run_id);
        setResults(resData);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, [projectId]);

  // Actions
  const handleUploadZip = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      await api.uploadProjectZip(projectId, file);
      await loadAllData();
      setActiveTab('artifacts');
      alert('Project ZIP archive extracted and scanned successfully!');
    } catch (err: any) {
      alert(err.message || 'Upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleUploadFolder = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    try {
      setUploading(true);
      await api.uploadFolderFiles(projectId, files);
      await loadAllData();
      setActiveTab('artifacts');
      alert(`Successfully scanned ${files.length} files from directory!`);
    } catch (err: any) {
      alert(err.message || 'Folder upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleLoadDemo = async () => {
    try {
      setLoadingDemo(true);
      await api.loadDemoProject(projectId);
      await loadAllData();
      alert('Demo Spring Boot & React benchmark project + 3 sample requirements loaded! You can now click "Run Verification".');
    } catch (err: any) {
      alert(err.message || 'Failed to load demo project');
    } finally {
      setLoadingDemo(false);
    }
  };

  const handleAddRequirement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newReqText.trim()) return;

    try {
      setAddingReq(true);
      await api.createRequirement(projectId, { requirement_text: newReqText });
      setNewReqText('');
      await loadAllData();
    } catch (err: any) {
      alert(err.message || 'Failed to add requirement');
    } finally {
      setAddingReq(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (requirements.length === 0) {
      alert('Please add at least one requirement before running verification.');
      setActiveTab('requirements');
      return;
    }

    try {
      setAnalyzing(true);
      const run = await api.triggerAnalysisRun(projectId);
      setLatestRun(run);
      const resData = await api.getAnalysisResults(run.analysis_run_id);
      setResults(resData);
      const graphData = await api.getRequirementGraph(projectId);
      setGraph(graphData);
      setActiveTab('dashboard');
    } catch (err: any) {
      alert(err.message || 'Analysis run failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const filteredResults = results.filter((r) => {
    if (statusFilter === 'ALL') return true;
    return r.status === statusFilter;
  });

  const contradictionCount = results.filter((r) => r.status === 'Contradictory').length;
  const missingCount = results.filter((r) => r.status === 'Missing').length;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full flex-1">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center gap-2 text-xs font-mono text-slate-500 mb-4">
          <button onClick={() => navigate('/projects')} className="hover:text-slate-800 flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" /> Projects
          </button>
          <span>/</span>
          <span className="text-slate-900 font-semibold">{project?.project_name || 'Project'}</span>
        </div>

        {/* Project Header Banner */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{project?.project_name}</h1>
              <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                {project?.source_version || 'v1.0.0'}
              </span>
            </div>
            <p className="text-sm text-slate-500 max-w-2xl">{project?.description || 'No description provided.'}</p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={handleLoadDemo}
              disabled={loadingDemo}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 rounded-lg text-xs font-semibold shadow-2xs transition"
              title="Auto-load pre-packaged Spring Boot & React benchmark with deliberate contradiction"
            >
              <Zap className="w-3.5 h-3.5 text-amber-600" />
              {loadingDemo ? 'Loading Demo...' : 'Load Benchmark Demo'}
            </button>

            <button
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold shadow-xs transition ${
                requirements.length > 0
                  ? 'bg-sky-600 hover:bg-sky-700 text-white'
                  : 'bg-slate-200 text-slate-500 hover:bg-slate-300'
              }`}
            >
              <Play className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
              {analyzing ? 'Evaluating Evidence...' : 'Run Verification'}
            </button>
          </div>
        </div>

        {/* 3-Step Onboarding & Verification Readiness Guide */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 mb-6 shadow-2xs">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 mb-3">
            Verification Workflow & Checklist
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Step 1: Upload */}
            <div className={`p-3.5 rounded-lg border flex items-start gap-3 transition ${
              artifacts.length > 0 ? 'bg-emerald-50/40 border-emerald-200' : 'bg-slate-50 border-slate-200'
            }`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                artifacts.length > 0 ? 'bg-emerald-600 text-white' : 'bg-slate-300 text-slate-700'
              }`}>
                {artifacts.length > 0 ? <Check className="w-3.5 h-3.5" /> : '1'}
              </div>
              <div className="flex-1">
                <p className="text-xs font-bold text-slate-900">1. Upload Software Artifacts</p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  {artifacts.length > 0 ? `${artifacts.length} files scanned` : 'Upload ZIP or select project folder'}
                </p>
                <button
                  onClick={() => setActiveTab('artifacts')}
                  className="mt-2 text-[11px] font-semibold text-sky-600 hover:underline flex items-center gap-0.5"
                >
                  Upload Files <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>

            {/* Step 2: Requirements */}
            <div className={`p-3.5 rounded-lg border flex items-start gap-3 transition ${
              requirements.length > 0 ? 'bg-emerald-50/40 border-emerald-200' : 'bg-slate-50 border-slate-200'
            }`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                requirements.length > 0 ? 'bg-emerald-600 text-white' : 'bg-slate-300 text-slate-700'
              }`}>
                {requirements.length > 0 ? <Check className="w-3.5 h-3.5" /> : '2'}
              </div>
              <div className="flex-1">
                <p className="text-xs font-bold text-slate-900">2. Define Requirements</p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  {requirements.length > 0 ? `${requirements.length} requirement(s) configured` : 'Add text requirements for AI decomposition'}
                </p>
                <button
                  onClick={() => setActiveTab('requirements')}
                  className="mt-2 text-[11px] font-semibold text-sky-600 hover:underline flex items-center gap-0.5"
                >
                  Manage Requirements <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>

            {/* Step 3: Run Verification */}
            <div className={`p-3.5 rounded-lg border flex items-start gap-3 transition ${
              results.length > 0 ? 'bg-sky-50/50 border-sky-200' : 'bg-slate-50 border-slate-200'
            }`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                results.length > 0 ? 'bg-sky-600 text-white' : 'bg-slate-300 text-slate-700'
              }`}>
                {results.length > 0 ? <Check className="w-3.5 h-3.5" /> : '3'}
              </div>
              <div className="flex-1">
                <p className="text-xs font-bold text-slate-900">3. Run Verification Engine</p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  {results.length > 0 ? `${results.length} claims verified` : 'Ready when requirements are defined'}
                </p>
                <button
                  onClick={handleRunAnalysis}
                  disabled={analyzing}
                  className="mt-2 text-[11px] font-semibold text-sky-600 hover:underline flex items-center gap-0.5"
                >
                  {analyzing ? 'Evaluating...' : 'Run Now'} <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200 mb-6 gap-2">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-2 py-3 px-4 text-sm font-semibold border-b-2 transition ${
              activeTab === 'dashboard'
                ? 'border-sky-600 text-sky-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <CheckCircle className="w-4 h-4" />
            Verification Dashboard
            {contradictionCount > 0 && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-rose-100 text-rose-700 font-bold">
                {contradictionCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('artifacts')}
            className={`flex items-center gap-2 py-3 px-4 text-sm font-semibold border-b-2 transition ${
              activeTab === 'artifacts'
                ? 'border-sky-600 text-sky-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Upload className="w-4 h-4" />
            Upload & Artifacts ({artifacts.length})
          </button>

          <button
            onClick={() => setActiveTab('requirements')}
            className={`flex items-center gap-2 py-3 px-4 text-sm font-semibold border-b-2 transition ${
              activeTab === 'requirements'
                ? 'border-sky-600 text-sky-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Layers className="w-4 h-4" />
            Requirements & Claims ({requirements.length})
          </button>

          <button
            onClick={() => setActiveTab('graph')}
            className={`flex items-center gap-2 py-3 px-4 text-sm font-semibold border-b-2 transition ${
              activeTab === 'graph'
                ? 'border-sky-600 text-sky-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <GitFork className="w-4 h-4" />
            Dependency Graph
          </button>

          <button
            onClick={() => setActiveTab('reports')}
            className={`flex items-center gap-2 py-3 px-4 text-sm font-semibold border-b-2 transition ${
              activeTab === 'reports'
                ? 'border-sky-600 text-sky-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <FileText className="w-4 h-4" />
            Reports & Export
          </button>
        </div>

        {/* TAB 1: VERIFICATION DASHBOARD */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Contradiction Warning Alert */}
            {contradictionCount > 0 && (
              <div className="p-4 rounded-xl bg-purple-50 border border-purple-200 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-purple-700 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-bold text-purple-900">
                    {contradictionCount} Material Artifact Contradiction(s) Detected!
                  </h4>
                  <p className="text-xs text-purple-700 mt-0.5">
                    Source code suggests functionality exists, but runtime API probing or test suite execution
                    demonstrated failure. Inspect the contradictory claims below for artifact provenance.
                  </p>
                </div>
              </div>
            )}

            {/* Metrics Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="bg-white p-4 rounded-xl border border-slate-200">
                <span className="text-[11px] font-mono uppercase text-slate-500 font-bold">Total Claims</span>
                <p className="text-2xl font-bold text-slate-900 mt-1">{results.length}</p>
              </div>
              <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/20">
                <span className="text-[11px] font-mono uppercase text-emerald-700 font-bold">Fully Satisfied</span>
                <p className="text-2xl font-bold text-emerald-700 mt-1">
                  {results.filter((r) => r.status === 'Fully Satisfied').length}
                </p>
              </div>
              <div className="bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/20">
                <span className="text-[11px] font-mono uppercase text-amber-700 font-bold">Partially Satisfied</span>
                <p className="text-2xl font-bold text-amber-700 mt-1">
                  {results.filter((r) => r.status === 'Partially Satisfied').length}
                </p>
              </div>
              <div className="bg-white p-4 rounded-xl border border-rose-200 bg-rose-50/20">
                <span className="text-[11px] font-mono uppercase text-rose-700 font-bold">Missing</span>
                <p className="text-2xl font-bold text-rose-700 mt-1">{missingCount}</p>
              </div>
              <div className="bg-white p-4 rounded-xl border border-purple-200 bg-purple-50/30">
                <span className="text-[11px] font-mono uppercase text-purple-700 font-bold">Contradictory</span>
                <p className="text-2xl font-bold text-purple-700 mt-1">{contradictionCount}</p>
              </div>
              <div className="bg-white p-4 rounded-xl border border-slate-200">
                <span className="text-[11px] font-mono uppercase text-slate-500 font-bold">Unverifiable</span>
                <p className="text-2xl font-bold text-slate-600 mt-1">
                  {results.filter((r) => r.status === 'Unverifiable').length}
                </p>
              </div>
            </div>

            {/* Filter Bar */}
            <div className="bg-white rounded-xl border border-slate-200 p-4 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-600 flex-wrap">
                <Filter className="w-4 h-4 text-slate-400" />
                <span>Filter by Status:</span>
                {['ALL', 'Contradictory', 'Fully Satisfied', 'Partially Satisfied', 'Missing', 'Unverifiable'].map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`px-2.5 py-1 rounded-md transition ${
                      statusFilter === st
                        ? 'bg-sky-600 text-white font-bold'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>

              {latestRun && (
                <div className="text-xs font-mono text-slate-400">
                  Analysis Run #{latestRun.analysis_run_id} ({latestRun.status})
                </div>
              )}
            </div>

            {/* Results Table */}
            {results.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-xl border border-dashed border-slate-300 p-6">
                <p className="text-sm font-semibold text-slate-700">No verification results available yet.</p>
                <p className="text-xs text-slate-500 mt-1 mb-4">
                  Add requirements and upload software artifacts, or click "Load Benchmark Demo" above!
                </p>
                <div className="flex justify-center gap-3">
                  <button
                    onClick={handleLoadDemo}
                    disabled={loadingDemo}
                    className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold shadow-xs"
                  >
                    Load Benchmark Demo
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase text-slate-500 font-mono">
                      <th className="py-3 px-4">Claim ID</th>
                      <th className="py-3 px-4">Atomic Claim Statement</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Sufficiency</th>
                      <th className="py-3 px-4">Evidence</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredResults.map((r) => (
                      <tr
                        key={r.result_id}
                        onClick={() => setSelectedResult(r)}
                        className="hover:bg-slate-50/80 cursor-pointer transition"
                      >
                        <td className="py-3.5 px-4 font-mono text-xs font-bold text-slate-500">
                          #{r.claim_id}
                        </td>
                        <td className="py-3.5 px-4 font-medium text-slate-900 max-w-md">
                          <p className="line-clamp-2">{r.claim_text}</p>
                          <p className="text-xs text-slate-500 mt-0.5 line-clamp-1 italic">{r.explanation}</p>
                        </td>
                        <td className="py-3.5 px-4">
                          <StatusBadge status={r.status} size="sm" />
                        </td>
                        <td className="py-3.5 px-4 font-mono text-xs text-slate-500 capitalize">
                          {r.sufficiency_state}
                        </td>
                        <td className="py-3.5 px-4 font-mono text-xs text-slate-600">
                          {r.evidence_records.length} items
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedResult(r);
                            }}
                            className="text-xs font-semibold text-sky-600 hover:text-sky-700 hover:underline"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: UPLOAD & ARTIFACT DISCOVERY */}
        {activeTab === 'artifacts' && (
          <div className="space-y-6">
            {/* Upload Options Card */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
              <h3 className="text-base font-bold text-slate-900 mb-1">Upload Project Artifacts</h3>
              <p className="text-xs text-slate-500 mb-6">
                You can upload your existing software project as a compressed ZIP file or select the project folder directly from your computer.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                {/* Option 1: ZIP Upload */}
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-sky-400 transition bg-slate-50/50 flex flex-col items-center justify-center">
                  <Upload className="w-8 h-8 text-sky-600 mb-2" />
                  <h4 className="text-sm font-bold text-slate-800">Upload ZIP Archive</h4>
                  <p className="text-xs text-slate-400 mb-3">Compress your project directory into a .zip file</p>
                  <label className="cursor-pointer">
                    <span className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-semibold shadow-xs inline-block">
                      {uploading ? 'Extracting...' : 'Select ZIP File'}
                    </span>
                    <input
                      type="file"
                      accept=".zip"
                      disabled={uploading}
                      onChange={handleUploadZip}
                      className="hidden"
                    />
                  </label>
                </div>

                {/* Option 2: Folder Directory Upload */}
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-indigo-400 transition bg-slate-50/50 flex flex-col items-center justify-center">
                  <FolderPlus className="w-8 h-8 text-indigo-600 mb-2" />
                  <h4 className="text-sm font-bold text-slate-800">Select Project Folder</h4>
                  <p className="text-xs text-slate-400 mb-3">Pick the root folder directly without zipping</p>
                  <label className="cursor-pointer">
                    <span className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs inline-block">
                      {uploading ? 'Scanning...' : 'Select Directory'}
                    </span>
                    <input
                      type="file"
                      /* @ts-ignore */
                      webkitdirectory=""
                      directory=""
                      multiple
                      disabled={uploading}
                      onChange={handleUploadFolder}
                      className="hidden"
                    />
                  </label>
                </div>
              </div>

              {/* Demo button option */}
              <div className="p-4 bg-amber-50 rounded-lg border border-amber-200 flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-amber-900">Don't have a project prepared right now?</h4>
                  <p className="text-[11px] text-amber-700">
                    Load the pre-packaged Spring Boot & React ground-truth benchmark app with 1 click.
                  </p>
                </div>
                <button
                  onClick={handleLoadDemo}
                  disabled={loadingDemo}
                  className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold shadow-2xs"
                >
                  {loadingDemo ? 'Loading...' : 'Load Benchmark Demo'}
                </button>
              </div>
            </div>

            {/* Discovered Artifacts Table */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
              <div className="p-4 border-b border-slate-200 flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-900">
                  Discovered Project Artifacts ({artifacts.length})
                </h3>
              </div>
              {artifacts.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-xs font-mono">
                  No artifacts uploaded yet. Use the upload cards above to scan your project.
                </div>
              ) : (
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase text-slate-500 font-mono">
                      <th className="py-3 px-4">Artifact Path</th>
                      <th className="py-3 px-4">Type</th>
                      <th className="py-3 px-4">Language</th>
                      <th className="py-3 px-4">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {artifacts.map((a) => (
                      <tr key={a.artifact_id} className="hover:bg-slate-50/80">
                        <td className="py-3 px-4 font-mono text-xs font-semibold text-slate-800">
                          {a.artifact_path}
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                            {a.artifact_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono text-xs text-slate-500">
                          {a.language || 'N/A'}
                        </td>
                        <td className="py-3 px-4 text-xs font-medium text-emerald-600">
                          {a.analysis_status}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: REQUIREMENTS & CLAIMS */}
        {activeTab === 'requirements' && (
          <div className="space-y-6">
            {/* Requirement Input Form */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
              <h3 className="text-base font-bold text-slate-900 mb-1">Add Natural-Language Requirement</h3>
              <p className="text-xs text-slate-500 mb-4">
                The Gemini AI decomposition engine will automatically break this requirement down into atomic, verifiable claims.
              </p>

              <form onSubmit={handleAddRequirement} className="space-y-4">
                <textarea
                  rows={3}
                  required
                  value={newReqText}
                  onChange={(e) => setNewReqText(e.target.value)}
                  placeholder="e.g. The system must reject expired authentication tokens. The frontend login form shall display an error notification."
                  className="block w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                />

                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={addingReq || !newReqText.trim()}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-sm font-semibold shadow-xs disabled:opacity-50"
                  >
                    <Sparkles className="w-4 h-4 text-sky-200" />
                    {addingReq ? 'Decomposing Claims...' : 'Add Requirement & Decompose'}
                  </button>
                </div>
              </form>
            </div>

            {/* Requirements List */}
            <div className="space-y-4">
              {requirements.map((req) => (
                <div key={req.requirement_id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <span className="text-xs font-mono font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded">
                      REQUIREMENT #{req.requirement_id}
                    </span>
                    <button
                      onClick={async () => {
                        await api.triggerDecomposition(req.requirement_id);
                        loadAllData();
                      }}
                      className="text-xs font-semibold text-slate-500 hover:text-sky-600 flex items-center gap-1"
                    >
                      <RefreshCw className="w-3.5 h-3.5" /> Re-decompose
                    </button>
                  </div>
                  <p className="text-sm font-semibold text-slate-900 mt-2.5">{req.requirement_text}</p>

                  {/* Atomic Claims */}
                  <div className="mt-4 pt-3 border-t border-slate-100">
                    <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 mb-2">
                      Atomic Verifiable Claims ({req.claims.length})
                    </h4>
                    <div className="space-y-2">
                      {req.claims.map((claim) => (
                        <div
                          key={claim.claim_id}
                          className="p-3 bg-slate-50 rounded-lg border border-slate-200/80 flex flex-col md:flex-row md:items-center justify-between gap-2"
                        >
                          <div>
                            <span className="text-[11px] font-mono font-bold text-indigo-700 mr-2">
                              CLAIM #{claim.claim_id}
                            </span>
                            <span className="text-xs font-medium text-slate-800">{claim.claim_text}</span>
                            {claim.expected_behavior && (
                              <p className="text-[11px] text-slate-500 italic mt-0.5">
                                Expected: {claim.expected_behavior}
                              </p>
                            )}
                          </div>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-500 shrink-0">
                            Artifacts: {claim.relevant_artifact_types}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: DEPENDENCY GRAPH */}
        {activeTab === 'graph' && graph && <RequirementGraphView graph={graph} />}

        {/* TAB 5: REPORTS & EXPORT */}
        {activeTab === 'reports' && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs max-w-2xl">
            <h3 className="text-base font-bold text-slate-900 mb-1">Download Verification Documentation</h3>
            <p className="text-xs text-slate-500 mb-6">
              Generate formal multi-artifact verification reports including audit traceability, contradiction evidence, and ground-truth metrics.
            </p>

            {latestRun ? (
              <div className="space-y-4">
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">PDF Verification Report</h4>
                    <p className="text-xs text-slate-500">Full audit documentation with summary tables and evidence references</p>
                  </div>
                  <a
                    href={api.getReportDownloadUrl(latestRun.analysis_run_id, 'pdf')}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-semibold shadow-xs"
                  >
                    Download PDF
                  </a>
                </div>

                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">CSV Data Export</h4>
                    <p className="text-xs text-slate-500">Tabular classification results and location references for research analysis</p>
                  </div>
                  <a
                    href={api.getReportDownloadUrl(latestRun.analysis_run_id, 'csv')}
                    download
                    className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold shadow-xs"
                  >
                    Download CSV
                  </a>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500 italic">
                No analysis runs recorded yet. Run verification first to generate reports.
              </p>
            )}
          </div>
        )}
      </main>

      {/* Evidence Drilldown Modal */}
      <EvidenceModal result={selectedResult} onClose={() => setSelectedResult(null)} />
    </div>
  );
};
