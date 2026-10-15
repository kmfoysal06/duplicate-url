"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  GlobeIcon,
  DownloadIcon,
  UploadIcon,
  AlertTriangleIcon,
  SparklesIcon,
} from "@/components/Icons";
import { JobStatusResponse, AnalysisResult } from "@/types/seo";
import PairsTable from "@/components/PairsTable";
import ClusterView from "@/components/ClusterView";
import DiffModal from "@/components/DiffModal";
import ActionPlanView from "@/components/ActionPlanView";
import TopicClustersView from "@/components/TopicClustersView";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Dashboard() {
  const [urlsText, setUrlsText] = useState<string>("");
  const [customTopicsText, setCustomTopicsText] = useState<string>("");
  const [showTopicsInput, setShowTopicsInput] = useState<boolean>(false);
  const [nearThreshold, setNearThreshold] = useState<number>(85.0);
  const [potentialThreshold, setPotentialThreshold] = useState<number>(70.0);
  const [respectRobots, setRespectRobots] = useState<boolean>(true);
  const [showSettings, setShowSettings] = useState<boolean>(false);

  // Job state
  const [jobId, setJobId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [selectedPairDiff, setSelectedPairDiff] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"topics" | "actions" | "pairs" | "clusters">("topics");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // URL count computation
  const urlCount = React.useMemo(() => {
    return urlsText
      .split("\n")
      .map((u) => u.trim())
      .filter((u) => u.length > 0 && !u.startsWith("#")).length;
  }, [urlsText]);

  // Load sample test suite URLs
  const handleLoadSampleUrls = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/sample-urls`);
      if (!res.ok) throw new Error("Could not fetch test URLs");
      const data = await res.json();
      setUrlsText(data.urls.join("\n"));
      if (data.sample_topics && data.sample_topics.length > 0) {
        setCustomTopicsText(data.sample_topics.join("\n"));
        setShowTopicsInput(true);
      }
      setErrorMsg(null);
    } catch {
      setErrorMsg("Failed to load test suite URLs. Please ensure the Python backend is running on port 8000.");
    }
  };

  // Handle File Upload (.csv or .txt)
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      if (!content) return;

      const lines = content
        .split(/[\r\n]+/)
        .map((l) => l.trim().replace(/^["']|["']$/g, ""))
        .filter((l) => l.length > 0 && (l.startsWith("http://") || l.startsWith("https://") || l.includes(".")));

      if (lines.length > 0) {
        setUrlsText((prev) => (prev ? `${prev}\n${lines.join("\n")}` : lines.join("\n")));
      }
    };
    reader.readAsText(file);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // Start Analysis
  const handleStartAnalysis = async () => {
    const urls = urlsText
      .split("\n")
      .map((u) => u.trim())
      .filter((u) => u.length > 0 && !u.startsWith("#"));

    if (urls.length === 0) {
      setErrorMsg("Please enter or upload at least one valid website URL.");
      return;
    }

    const userTopics = customTopicsText
      .split("\n")
      .map((t) => t.trim())
      .filter((t) => t.length > 0 && !t.startsWith("#"));

    setErrorMsg(null);
    setIsSubmitting(true);
    setJobStatus(null);

    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          urls,
          user_topics: userTopics.length > 0 ? userTopics : null,
          near_threshold: nearThreshold,
          potential_threshold: potentialThreshold,
          respect_robots: respectRobots,
          allow_local_for_testing: urls.some((u) => u.includes("127.0.0.1") || u.includes("localhost")),
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: "Analysis failed to start" }));
        throw new Error(errData.detail || "Analysis request failed.");
      }

      const data = await res.json();
      setJobId(data.job_id);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to start analysis job.";
      setErrorMsg(message);
      setIsSubmitting(false);
    }
  };

  // Poll Job Status
  useEffect(() => {
    if (!jobId) return;

    let isMounted = true;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
        if (!res.ok) return;
        const data: JobStatusResponse = await res.json();

        if (isMounted) {
          setJobStatus(data);
          if (data.status === "completed" || data.status === "failed") {
            setIsSubmitting(false);
            clearInterval(interval);
          }
        }
      } catch {
        // Keep polling if transient network hiccup
      }
    }, 800);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [jobId]);

  // Export CSV
  const handleExportCSV = () => {
    if (!jobId) return;
    window.location.href = `${API_BASE}/api/jobs/${jobId}/export`;
  };

  const results: AnalysisResult | null = jobStatus?.results || null;
  const summary = results?.summary;

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 flex flex-col font-sans">
      
      {/* Top Navbar */}
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-indigo-600 text-white shadow-xs">
              <GlobeIcon className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-bold text-zinc-900 dark:text-white leading-tight">
                SEO Duplicate-Page Detection System
              </h1>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                MinHash LSH • Semantic Extraction • Canonical Auditing
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleLoadSampleUrls}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-indigo-200 dark:border-indigo-900 bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900 transition flex items-center gap-1.5"
            >
              <SparklesIcon className="w-3.5 h-3.5" />
              Load Sample SEO Suite
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">

        {/* Input Panel Card */}
        <section className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-2xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-bold text-zinc-900 dark:text-white uppercase tracking-wider">
                Target Website URLs
              </h2>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Paste URLs (one per line) or upload a CSV or TXT sitemap file.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700">
                {urlCount} {urlCount === 1 ? "URL" : "URLs"} entered
              </span>

              {/* Hidden File Input */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.txt"
                onChange={handleFileUpload}
                className="hidden"
              />
              
              <button
                onClick={() => fileInputRef.current?.click()}
                className="text-xs font-medium px-3 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 transition flex items-center gap-1.5"
              >
                <UploadIcon className="w-3.5 h-3.5" />
                Upload CSV / TXT
              </button>

              <button
                onClick={() => setShowSettings(!showSettings)}
                className="text-xs font-medium px-3 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 transition"
              >
                {showSettings ? "Hide Settings" : "Crawl & Threshold Settings"}
              </button>
            </div>
          </div>

          {/* Text Area */}
          <textarea
            rows={5}
            value={urlsText}
            onChange={(e) => setUrlsText(e.target.value)}
            placeholder="https://example.com/page-1&#10;https://example.com/page-2&#10;https://example.com/category/product?color=blue"
            className="w-full p-3 font-mono text-xs rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
          />

          {/* Target Topics / Content Hubs (Optional) */}
          <div className="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-200 dark:border-zinc-800 space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-zinc-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
                  <SparklesIcon className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
                  Target Topics / Content Hubs (Optional)
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                  {customTopicsText.split("\n").map((t) => t.trim()).filter(Boolean).length > 0
                    ? `${customTopicsText.split("\n").map((t) => t.trim()).filter(Boolean).length} Target Topics Specified`
                    : "Automatic AI Topic Detection"}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setShowTopicsInput(!showTopicsInput)}
                className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
              >
                {showTopicsInput ? "Hide Topics Input" : "Define Custom Topics"}
              </button>
            </div>

            {(showTopicsInput || customTopicsText.trim().length > 0) && (
              <div className="space-y-1.5 pt-1">
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                  Enter target topics or keyword themes (one per line). The engine will classify URLs into these topics. Leave blank to let AI auto-detect topics from page text and headings.
                </p>
                <textarea
                  rows={3}
                  value={customTopicsText}
                  onChange={(e) => setCustomTopicsText(e.target.value)}
                  placeholder="Technical SEO Audits&#10;Commercial Roofing Services&#10;Digital Marketing Strategy"
                  className="w-full p-2.5 font-mono text-xs rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                />
              </div>
            )}
          </div>

          {/* Collapsible Settings */}
          {showSettings && (
            <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-200 dark:border-zinc-700 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div>
                <label className="font-semibold block mb-1 text-zinc-700 dark:text-zinc-300">
                  Near Duplicate Threshold ({nearThreshold}%)
                </label>
                <input
                  type="range"
                  min="75"
                  max="98"
                  value={nearThreshold}
                  onChange={(e) => setNearThreshold(parseFloat(e.target.value))}
                  className="w-full"
                />
                <span className="text-[11px] text-zinc-400">Default: 85% similarity</span>
              </div>

              <div>
                <label className="font-semibold block mb-1 text-zinc-700 dark:text-zinc-300">
                  Potential Duplicate Threshold ({potentialThreshold}%)
                </label>
                <input
                  type="range"
                  min="55"
                  max="80"
                  value={potentialThreshold}
                  onChange={(e) => setPotentialThreshold(parseFloat(e.target.value))}
                  className="w-full"
                />
                <span className="text-[11px] text-zinc-400">Default: 70% similarity</span>
              </div>

              <div className="flex flex-col justify-center">
                <label className="flex items-center gap-2 cursor-pointer font-semibold text-zinc-700 dark:text-zinc-300">
                  <input
                    type="checkbox"
                    checked={respectRobots}
                    onChange={(e) => setRespectRobots(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                  />
                  <span>Respect robots.txt rules</span>
                </label>
                <span className="text-[11px] text-zinc-400 mt-1">Prevents crawling disallowed paths</span>
              </div>
            </div>
          )}

          {/* Action Row */}
          <div className="flex items-center justify-between pt-2">
            <div>
              {errorMsg && (
                <p className="text-xs text-red-600 dark:text-red-400 font-medium flex items-center gap-1.5">
                  <AlertTriangleIcon className="w-4 h-4 shrink-0" />
                  {errorMsg}
                </p>
              )}
            </div>

            <button
              onClick={handleStartAnalysis}
              disabled={isSubmitting || urlCount === 0}
              className={`px-6 py-2.5 rounded-xl font-bold text-xs text-white shadow-sm transition flex items-center gap-2 ${
                isSubmitting || urlCount === 0
                  ? "bg-zinc-400 dark:bg-zinc-700 cursor-not-allowed"
                  : "bg-indigo-600 hover:bg-indigo-500 active:scale-98"
              }`}
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Analyzing Pages...
                </>
              ) : (
                <>
                  <GlobeIcon className="w-4 h-4" />
                  Analyze Pages
                </>
              )}
            </button>
          </div>
        </section>

        {/* Live Progress Bar (when running) */}
        {isSubmitting && jobStatus && (
          <section className="p-5 rounded-2xl bg-indigo-50/70 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-900/60 shadow-2xs space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-indigo-900 dark:text-indigo-200">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-indigo-600 animate-ping"></span>
                {jobStatus.progress.stage}: {jobStatus.progress.message}
              </span>
              <span>{jobStatus.progress.percent}%</span>
            </div>

            <div className="w-full bg-indigo-200/80 dark:bg-indigo-900/60 h-2.5 rounded-full overflow-hidden">
              <div
                className="bg-indigo-600 h-full rounded-full transition-all duration-300"
                style={{ width: `${jobStatus.progress.percent}%` }}
              />
            </div>

            {jobStatus.progress.current_url && (
              <p className="text-[11px] font-mono text-zinc-500 dark:text-zinc-400 truncate">
                Fetching: {jobStatus.progress.current_url}
              </p>
            )}
          </section>
        )}

        {/* Results Dashboard Section */}
        {results && summary && (
          <div className="space-y-6">

            {/* Summary Cards Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
              {[
                { label: "Submitted", val: summary.total_urls_submitted, color: "text-zinc-900 dark:text-white" },
                { label: "Crawled (200 OK)", val: summary.successfully_crawled, color: "text-emerald-600 dark:text-emerald-400" },
                { label: "Failed / Blocked", val: summary.failed_urls, color: "text-red-600 dark:text-red-400" },
                { label: "Exact Duplicates", val: summary.exact_duplicate_groups, color: "text-rose-600 dark:text-rose-400" },
                { label: "Near Duplicates", val: summary.near_duplicate_groups, color: "text-orange-600 dark:text-orange-400" },
                { label: "Potential Dups", val: summary.potential_duplicate_groups, color: "text-amber-600 dark:text-amber-400" },
                { label: "Shared Canonicals", val: summary.pages_sharing_canonicals, color: "text-indigo-600 dark:text-indigo-400" },
              ].map((card, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-2xs"
                >
                  <p className="text-[11px] font-bold uppercase tracking-wider text-zinc-400 truncate">
                    {card.label}
                  </p>
                  <p className={`text-xl font-extrabold mt-1 ${card.color}`}>
                    {card.val}
                  </p>
                </div>
              ))}
            </div>

            {/* View Mode Switcher and Export Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-xl bg-zinc-200/80 dark:bg-zinc-800/80">
                <button
                  onClick={() => setViewMode("topics")}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
                    viewMode === "topics"
                      ? "bg-white dark:bg-zinc-900 text-indigo-600 dark:text-indigo-400 shadow-2xs"
                      : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900"
                  }`}
                >
                  <SparklesIcon className="w-3.5 h-3.5 text-indigo-500" />
                  Topic & Intent Clusters ({results.topic_clusters?.clusters?.length || 0})
                </button>
                <button
                  onClick={() => setViewMode("actions")}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
                    viewMode === "actions"
                      ? "bg-white dark:bg-zinc-900 text-indigo-600 dark:text-indigo-400 shadow-2xs"
                      : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900"
                  }`}
                >
                  Consolidation Action Plan ({results.consolidation_plan?.actions?.length || 0})
                </button>
                <button
                  onClick={() => setViewMode("pairs")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                    viewMode === "pairs"
                      ? "bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white shadow-2xs"
                      : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900"
                  }`}
                >
                  All Evaluated Pairs ({results.pairs.length})
                </button>
                <button
                  onClick={() => setViewMode("clusters")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                    viewMode === "clusters"
                      ? "bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white shadow-2xs"
                      : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900"
                  }`}
                >
                  Content Duplicates ({results.clusters.length})
                </button>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <a
                  href={`${API_BASE}/api/jobs/${jobId}/export-topic-clusters`}
                  className="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-xs transition flex items-center gap-1.5"
                >
                  <DownloadIcon className="w-3.5 h-3.5" />
                  Topic Clusters CSV
                </a>
                <a
                  href={`${API_BASE}/api/jobs/${jobId}/export-actions`}
                  className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-zinc-200 hover:bg-zinc-300 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 shadow-xs transition flex items-center gap-1.5"
                >
                  <DownloadIcon className="w-3.5 h-3.5" />
                  Action Plan CSV
                </a>
                <button
                  onClick={handleExportCSV}
                  className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-zinc-200 hover:bg-zinc-300 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 shadow-xs transition flex items-center gap-1.5"
                >
                  <DownloadIcon className="w-3.5 h-3.5" />
                  Full Audit CSV
                </button>
              </div>
            </div>

            {/* View Render */}
            {viewMode === "topics" ? (
              <TopicClustersView
                topicData={results.topic_clusters}
                jobId={jobId!}
                apiBase={API_BASE}
              />
            ) : viewMode === "actions" ? (
              <ActionPlanView
                plan={results.consolidation_plan}
                jobId={jobId!}
                apiBase={API_BASE}
              />
            ) : viewMode === "pairs" ? (
              <PairsTable
                pairs={results.pairs}
                onOpenDiff={(pairId) => setSelectedPairDiff(pairId)}
              />
            ) : (
              <ClusterView
                clusters={results.clusters}
                pairs={results.pairs}
                pages={results.pages}
                onOpenDiff={(pairId) => setSelectedPairDiff(pairId)}
              />
            )}

          </div>
        )}

      </main>

      {/* Side-by-Side Diff Modal */}
      {selectedPairDiff && jobId && (
        <DiffModal
          jobId={jobId}
          pairId={selectedPairDiff}
          onClose={() => setSelectedPairDiff(null)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-zinc-200 dark:border-zinc-800 py-4 px-6 text-center text-xs text-zinc-500 dark:text-zinc-400">
        SEO Duplicate-Page Detection System • Built for Professional SEO Auditing
      </footer>

    </div>
  );
}
