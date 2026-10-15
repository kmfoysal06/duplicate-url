"use client";

import React, { useState, useMemo } from "react";
import { ConsolidationPlan, ConsolidationAction } from "@/types/seo";
import { SearchIcon, ExternalLinkIcon, DownloadIcon, CheckCircleIcon, AlertTriangleIcon } from "./Icons";

interface ActionPlanViewProps {
  plan?: ConsolidationPlan;
  jobId: string;
  apiBase: string;
}

export default function ActionPlanView({ plan, jobId, apiBase }: ActionPlanViewProps) {
  const [filterAction, setFilterAction] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [showConfigModal, setShowConfigModal] = useState<boolean>(false);
  const [activeConfigTab, setActiveConfigTab] = useState<"apache" | "nginx" | "cloudflare">("apache");

  const actions = plan?.actions || [];
  const summary = plan?.summary;

  const filteredActions = useMemo(() => {
    return actions.filter((a) => {
      if (filterAction !== "ALL" && a.action !== filterAction) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchSrc = a.source_url.toLowerCase().includes(q);
        const matchTgt = (a.target_url || "").toLowerCase().includes(q);
        const matchReason = a.reason.toLowerCase().includes(q);
        if (!matchSrc && !matchTgt && !matchReason) return false;
      }
      return true;
    });
  }, [actions, filterAction, searchQuery]);

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(label);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const getActionBadge = (action: ConsolidationAction["action"]) => {
    switch (action) {
      case "301_REDIRECT":
        return {
          bg: "bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-950/60 dark:text-purple-300 dark:border-purple-800",
          label: "301 Redirect",
          dot: "bg-purple-500",
        };
      case "MERGE_AND_REDIRECT":
        return {
          bg: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-800",
          label: "Merge & Redirect",
          dot: "bg-blue-500",
        };
      case "PRUNE_OR_DELETE":
        return {
          bg: "bg-rose-100 text-rose-800 border-rose-200 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800",
          label: "Delete / 410 Gone",
          dot: "bg-rose-500",
        };
      case "CANONICALIZE":
        return {
          bg: "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800",
          label: "Add rel='canonical'",
          dot: "bg-amber-500",
        };
      case "DIFFERENTIATE":
        return {
          bg: "bg-cyan-100 text-cyan-800 border-cyan-200 dark:bg-cyan-950/60 dark:text-cyan-300 dark:border-cyan-800",
          label: "Keep & Differentiate",
          dot: "bg-cyan-500",
        };
      case "KEEP_PRIMARY":
        return {
          bg: "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800",
          label: "Master Pillar Page",
          dot: "bg-emerald-500",
        };
    }
  };

  const getPriorityBadge = (priority: "High" | "Medium" | "Low") => {
    switch (priority) {
      case "High":
        return "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/50 dark:text-red-300";
      case "Medium":
        return "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/50 dark:text-amber-300";
      case "Low":
        return "bg-zinc-100 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400";
    }
  };

  if (!plan || actions.length === 0) {
    return (
      <div className="p-12 text-center rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        <p className="text-zinc-500 dark:text-zinc-400 text-sm">
          No consolidation actions necessary. All pages appear unique or properly isolated.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Summary KPI Cards */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3.5 rounded-xl bg-purple-50/60 dark:bg-purple-950/30 border border-purple-200/80 dark:border-purple-900/60 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-purple-700 dark:text-purple-300">
              301 Redirects
            </p>
            <p className="text-2xl font-extrabold text-purple-900 dark:text-purple-100 mt-1">
              {summary.to_redirect_301}
            </p>
            <span className="text-[10px] text-purple-600 dark:text-purple-400">Consolidate equity</span>
          </div>

          <div className="p-3.5 rounded-xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200/80 dark:border-blue-900/60 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-blue-700 dark:text-blue-300">
              Merge & Redirect
            </p>
            <p className="text-2xl font-extrabold text-blue-900 dark:text-blue-100 mt-1">
              {summary.to_merge_and_redirect}
            </p>
            <span className="text-[10px] text-blue-600 dark:text-blue-400">Combine unique copy</span>
          </div>

          <div className="p-3.5 rounded-xl bg-rose-50/60 dark:bg-rose-950/30 border border-rose-200/80 dark:border-rose-900/60 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-rose-700 dark:text-rose-300">
              Delete / 410 Gone
            </p>
            <p className="text-2xl font-extrabold text-rose-900 dark:text-rose-100 mt-1">
              {summary.to_prune_or_delete}
            </p>
            <span className="text-[10px] text-rose-600 dark:text-rose-400">Prune thin pages</span>
          </div>

          <div className="p-3.5 rounded-xl bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200/80 dark:border-amber-900/60 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-300">
              Canonicalize
            </p>
            <p className="text-2xl font-extrabold text-amber-900 dark:text-amber-100 mt-1">
              {summary.to_canonicalize}
            </p>
            <span className="text-[10px] text-amber-600 dark:text-amber-400">Keep live for UX</span>
          </div>

          <div className="p-3.5 rounded-xl bg-cyan-50/60 dark:bg-cyan-950/30 border border-cyan-200/80 dark:border-cyan-900/60 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-cyan-700 dark:text-cyan-300">
              Differentiate
            </p>
            <p className="text-2xl font-extrabold text-cyan-900 dark:text-cyan-100 mt-1">
              {summary.to_differentiate}
            </p>
            <span className="text-[10px] text-cyan-600 dark:text-cyan-400">Add local details</span>
          </div>

          <div className="p-3.5 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200/80 dark:border-emerald-900/60 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">
              Master Pages
            </p>
            <p className="text-2xl font-extrabold text-emerald-900 dark:text-emerald-100 mt-1">
              {summary.primary_master_pages}
            </p>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400">Designated winners</span>
          </div>
        </div>
      )}

      {/* Control Bar: Filter, Search, Export Config, Download CSV */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800">
        
        {/* Search */}
        <div className="relative flex-1 min-w-[220px]">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-400">
            <SearchIcon className="w-4 h-4" />
          </div>
          <input
            type="text"
            placeholder="Search action by URL or reason..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Action Type Filter Buttons */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          {[
            { label: "All Actions", val: "ALL" },
            { label: "301 Redirects", val: "301_REDIRECT" },
            { label: "Merge & 301", val: "MERGE_AND_REDIRECT" },
            { label: "Delete / 410", val: "PRUNE_OR_DELETE" },
            { label: "Canonicalize", val: "CANONICALIZE" },
            { label: "Master Pillar", val: "KEEP_PRIMARY" },
          ].map((btn) => (
            <button
              key={btn.val}
              onClick={() => setFilterAction(btn.val)}
              className={`px-3 py-1 rounded-lg font-medium transition ${
                filterAction === btn.val
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "bg-white dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-700"
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>

        {/* Action Buttons: Server Code Snippets + CSV Download */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowConfigModal(true)}
            className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-zinc-200 hover:bg-zinc-300 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 transition"
          >
            Get Server Redirect Rules
          </button>

          <a
            href={`${apiBase}/api/jobs/${jobId}/export-actions`}
            className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-2xs transition flex items-center gap-1.5"
          >
            <DownloadIcon className="w-3.5 h-3.5" />
            Download Action Plan CSV
          </a>
        </div>

      </div>

      {/* Action Cards List */}
      <div className="space-y-3.5">
        {filteredActions.length === 0 ? (
          <div className="p-8 text-center bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-400">
            No matching actions found for the current search/filter.
          </div>
        ) : (
          filteredActions.map((item, idx) => {
            const badge = getActionBadge(item.action);

            return (
              <div
                key={idx}
                className="p-5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-2xs space-y-3 hover:border-zinc-300 dark:hover:border-zinc-700 transition"
              >
                {/* Card Top: Badges and Cluster Info */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${badge.bg}`}
                    >
                      <span className={`w-2 h-2 rounded-full ${badge.dot}`} />
                      {badge.label}
                    </span>

                    <span
                      className={`px-2 py-0.5 rounded-md text-[11px] font-semibold border ${getPriorityBadge(
                        item.priority
                      )}`}
                    >
                      {item.priority} Priority
                    </span>

                    <span className="text-xs text-zinc-400 font-medium">
                      Cluster: {item.cluster_id}
                    </span>
                  </div>

                  <div className="text-[11px] text-zinc-400 flex items-center gap-3">
                    <span>Status: {item.status_code || "ERR"}</span>
                    <span>{item.word_count} words</span>
                  </div>
                </div>

                {/* URL Routing Representation */}
                <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-200/80 dark:border-zinc-700/80 text-xs space-y-2">
                  
                  {/* Source URL */}
                  <div className="flex items-center gap-2">
                    <span className="w-16 shrink-0 font-bold uppercase text-[10px] text-zinc-400">Source:</span>
                    <a
                      href={item.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="font-mono text-blue-600 dark:text-blue-400 font-semibold hover:underline break-all flex items-center gap-1"
                    >
                      <span>{item.source_url}</span>
                      <ExternalLinkIcon className="w-3 h-3 shrink-0 opacity-60" />
                    </a>
                  </div>

                  {/* Target URL (if applicable) */}
                  {item.target_url && (
                    <div className="flex items-center gap-2 pt-1 border-t border-zinc-200/60 dark:border-zinc-700/60">
                      <span className="w-16 shrink-0 font-bold uppercase text-[10px] text-emerald-600 dark:text-emerald-400">
                        Target URL:
                      </span>
                      <a
                        href={item.target_url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-mono text-emerald-600 dark:text-emerald-400 font-semibold hover:underline break-all flex items-center gap-1"
                      >
                        <span>{item.target_url}</span>
                        <ExternalLinkIcon className="w-3 h-3 shrink-0 opacity-60" />
                      </a>
                    </div>
                  )}

                </div>

                {/* Recommendation Rationale */}
                <div className="text-xs leading-relaxed text-zinc-700 dark:text-zinc-300 bg-zinc-50/50 dark:bg-zinc-800/30 p-3 rounded-lg border border-zinc-100 dark:border-zinc-800">
                  <span className="font-bold text-zinc-900 dark:text-white mr-1.5">
                    Why this action & target:
                  </span>
                  {item.reason}
                </div>

              </div>
            );
          })
        )}
      </div>

      {/* Server Rules Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="w-full max-w-3xl bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-800 overflow-hidden">
            
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-200 dark:border-zinc-800">
              <div>
                <h3 className="text-base font-bold text-zinc-900 dark:text-white">
                  Server Redirect Directives
                </h3>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  Ready-to-paste 301 redirect configuration for your web server or CDN
                </p>
              </div>
              <button
                onClick={() => setShowConfigModal(false)}
                className="text-zinc-400 hover:text-zinc-700 dark:hover:text-white text-sm font-bold"
              >
                ✕
              </button>
            </div>

            {/* Modal Tabs */}
            <div className="flex gap-2 px-6 pt-3 border-b border-zinc-200 dark:border-zinc-800">
              {[
                { id: "apache", label: "Apache (.htaccess)" },
                { id: "nginx", label: "Nginx rewrite" },
                { id: "cloudflare", label: "Cloudflare Bulk CSV" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveConfigTab(tab.id as any)}
                  className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition ${
                    activeConfigTab === tab.id
                      ? "border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400"
                      : "border-transparent text-zinc-500 hover:text-zinc-800"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Code Box */}
            <div className="p-6 space-y-4">
              <div className="relative">
                <pre className="p-4 rounded-xl bg-zinc-950 text-zinc-200 font-mono text-xs max-h-72 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                  {activeConfigTab === "apache" && (plan?.export_snippets?.apache || "")}
                  {activeConfigTab === "nginx" && (plan?.export_snippets?.nginx || "")}
                  {activeConfigTab === "cloudflare" && (plan?.export_snippets?.cloudflare_csv || "")}
                </pre>

                <button
                  onClick={() => {
                    const text =
                      activeConfigTab === "apache"
                        ? plan?.export_snippets?.apache || ""
                        : activeConfigTab === "nginx"
                        ? plan?.export_snippets?.nginx || ""
                        : plan?.export_snippets?.cloudflare_csv || "";
                    handleCopy(text, activeConfigTab);
                  }}
                  className="absolute top-3 right-3 px-3 py-1.5 rounded-lg text-xs font-semibold bg-zinc-800 hover:bg-zinc-700 text-white transition flex items-center gap-1.5"
                >
                  {copiedCode === activeConfigTab ? (
                    <>
                      <CheckCircleIcon className="w-3.5 h-3.5 text-emerald-400" />
                      Copied!
                    </>
                  ) : (
                    "Copy Snippet"
                  )}
                </button>
              </div>

              <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                <strong>SEO Best Practice:</strong> 301 redirects permanently transfer historical link equity and search rankings to the target master URL. Verify that target URLs return HTTP 200 OK before deploying.
              </p>
            </div>

            {/* Footer */}
            <div className="flex justify-end px-6 py-3 border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/60">
              <button
                onClick={() => setShowConfigModal(false)}
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-zinc-200 hover:bg-zinc-300 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200"
              >
                Close
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
