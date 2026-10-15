"use client";

import React, { useState, useMemo } from "react";
import { TopicClustersResult, TopicClusterPage } from "@/types/seo";
import { SearchIcon, DownloadIcon, SparklesIcon, LayersIcon, AlertTriangleIcon } from "./Icons";

interface TopicClustersViewProps {
  topicData?: TopicClustersResult;
  jobId: string;
  apiBase: string;
}

export default function TopicClustersView({ topicData, jobId, apiBase }: TopicClustersViewProps) {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [showMultiOnly, setShowMultiOnly] = useState<boolean>(true);
  const [expandedCluster, setExpandedCluster] = useState<string | null>(null);

  const clusters = useMemo(() => topicData?.clusters || [], [topicData?.clusters]);
  const summary = topicData?.summary;

  const filteredClusters = useMemo(() => {
    return clusters.filter((c) => {
      if (showMultiOnly && c.member_count <= 1) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchTopic = c.topic.toLowerCase().includes(q);
        const matchUrls = c.pages.some((p) => p.url.toLowerCase().includes(q) || p.title.toLowerCase().includes(q));
        if (!matchTopic && !matchUrls) return false;
      }
      return true;
    });
  }, [clusters, showMultiOnly, searchQuery]);

  // Set default expanded cluster
  React.useEffect(() => {
    if (filteredClusters.length > 0 && !expandedCluster) {
      setExpandedCluster(filteredClusters[0].cluster_id);
    }
  }, [filteredClusters, expandedCluster]);

  const getIntentBadge = (intent: string) => {
    switch (intent) {
      case "Informational":
        return "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-950/60 dark:text-blue-300";
      case "Commercial":
        return "bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-950/60 dark:text-purple-300";
      case "Transactional":
        return "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300";
      case "Navigational / Local":
        return "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-950/60 dark:text-amber-300";
      default:
        return "bg-zinc-100 text-zinc-700 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-300";
    }
  };

  const getActionBadge = (action: TopicClusterPage["action"]) => {
    switch (action) {
      case "KEEP_PRIMARY":
        return {
          cls: "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300",
          label: "Master Pillar Page",
        };
      case "301_REDIRECT":
        return {
          cls: "bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-950/60 dark:text-purple-300",
          label: "301 Redirect",
        };
      case "MERGE_CONTENT":
        return {
          cls: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-950/60 dark:text-blue-300",
          label: "Merge Content & 301",
        };
      case "DELETE_OR_PRUNE":
        return {
          cls: "bg-rose-100 text-rose-800 border-rose-200 dark:bg-rose-950/60 dark:text-rose-300",
          label: "Delete / 410",
        };
      case "KEEP_SEPARATE":
        return {
          cls: "bg-cyan-100 text-cyan-800 border-cyan-200 dark:bg-cyan-950/60 dark:text-cyan-300",
          label: "Keep Separate (Unique Intent)",
        };
      case "IMPROVE_CONTENT":
        return {
          cls: "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-950/60 dark:text-amber-300",
          label: "Improve & Differentiate",
        };
    }
  };

  if (!topicData || clusters.length === 0) {
    return (
      <div className="p-12 text-center rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        <p className="text-zinc-500 dark:text-zinc-400 text-sm">
          No topic clusters identified. Crawl pages to generate multi-signal clusters.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Top Topic Cluster Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
          <div className="p-3.5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Topic Clusters
            </p>
            <p className="text-2xl font-extrabold text-zinc-900 dark:text-white mt-1">
              {summary.total_topic_clusters}
            </p>
            <span className="text-[10px] text-zinc-500">Grouped by intent & slug</span>
          </div>

          <div className="p-3.5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
              Master Pages
            </p>
            <p className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-1">
              {summary.total_primary_master_urls}
            </p>
            <span className="text-[10px] text-emerald-600/80">Elected primary targets</span>
          </div>

          <div className="p-3.5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-purple-600 dark:text-purple-400">
              301 Redirects
            </p>
            <p className="text-2xl font-extrabold text-purple-600 dark:text-purple-400 mt-1">
              {summary.total_recommended_redirects}
            </p>
            <span className="text-[10px] text-purple-600/80">Exact / parameter dups</span>
          </div>

          <div className="p-3.5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
              Merge & Redirect
            </p>
            <p className="text-2xl font-extrabold text-blue-600 dark:text-blue-400 mt-1">
              {summary.total_recommended_merges}
            </p>
            <span className="text-[10px] text-blue-600/80">Consolidate pillar pages</span>
          </div>

          <div className="p-3.5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400">
              Delete / Prune
            </p>
            <p className="text-2xl font-extrabold text-rose-600 dark:text-rose-400 mt-1">
              {summary.total_recommended_pruning}
            </p>
            <span className="text-[10px] text-rose-600/80">Thin / broken URLs</span>
          </div>

          <div className="p-3.5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400">
              Keep Separate
            </p>
            <p className="text-2xl font-extrabold text-cyan-600 dark:text-cyan-400 mt-1">
              {summary.total_keep_separate}
            </p>
            <span className="text-[10px] text-cyan-600/80">Distinct user intents</span>
          </div>
        </div>
      )}

      {/* Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800">
        
        {/* Search */}
        <div className="relative flex-1 min-w-[220px]">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-400">
            <SearchIcon className="w-4 h-4" />
          </div>
          <input
            type="text"
            placeholder="Search topic or URL..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Toggle Multi-Page only */}
        <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-zinc-700 dark:text-zinc-300">
          <input
            type="checkbox"
            checked={showMultiOnly}
            onChange={(e) => setShowMultiOnly(e.target.checked)}
            className="rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4"
          />
          <span>Show Multi-URL Topic Groups Only ({clusters.filter(c => c.member_count > 1).length})</span>
        </label>

        {/* Export Button */}
        <a
          href={`${apiBase}/api/jobs/${jobId}/export-topic-clusters`}
          className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-2xs transition flex items-center gap-1.5"
        >
          <DownloadIcon className="w-3.5 h-3.5" />
          Export Topic Clusters CSV
        </a>

      </div>

      {/* Topic Cluster Cards */}
      <div className="space-y-4">
        {filteredClusters.length === 0 ? (
          <div className="p-8 text-center bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-400">
            No matching topic clusters found.
          </div>
        ) : (
          filteredClusters.map((cluster) => {
            const isExpanded = expandedCluster === cluster.cluster_id;

            return (
              <div
                key={cluster.cluster_id}
                className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden shadow-2xs"
              >
                {/* Cluster Header */}
                <div
                  onClick={() => setExpandedCluster(isExpanded ? null : cluster.cluster_id)}
                  className="p-5 flex flex-wrap items-center justify-between gap-3 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800/40 transition select-none"
                >
                  <div className="flex items-center gap-3">
                    <span className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
                      <LayersIcon className="w-5 h-5" />
                    </span>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-xs font-bold uppercase tracking-wider text-zinc-400">
                          {cluster.cluster_id}
                        </span>
                        <h3 className="text-base font-bold text-zinc-900 dark:text-white">
                          Target Topic: {cluster.topic}
                        </h3>
                        {cluster.topic_source === "USER_DEFINED" ? (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 flex items-center gap-1">
                            <SparklesIcon className="w-3 h-3 text-indigo-600 dark:text-indigo-400" />
                            User-Defined Topic
                          </span>
                        ) : (
                          <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700">
                            AI Auto-Detected
                          </span>
                        )}
                      </div>
                      
                      <div className="flex flex-wrap items-center gap-2 mt-1">
                        <span className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">
                          {cluster.member_count} competing pages
                        </span>
                        <span className="text-zinc-400">•</span>
                        {/* Search intent pills */}
                        {Object.entries(cluster.search_intents).map(([intent, count]) => (
                          <span
                            key={intent}
                            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${getIntentBadge(intent)}`}
                          >
                            {intent} ({count})
                          </span>
                        ))}
                        {cluster.has_intent_conflict && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300 flex items-center gap-1">
                            <AlertTriangleIcon className="w-3 h-3" />
                            Intent Conflict
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                    {isExpanded ? "Collapse" : "Review Cluster Analysis"}
                  </div>
                </div>

                {/* Expanded Cluster Table & Action Details */}
                {isExpanded && (
                  <div className="px-5 pb-5 pt-2 border-t border-zinc-100 dark:border-zinc-800 space-y-4">
                    
                    {/* Primary Elected Master Banner */}
                    <div className="p-3.5 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/60 flex flex-wrap items-center justify-between gap-2">
                      <div className="space-y-0.5">
                        <span className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-800 dark:text-emerald-300">
                          Elected Primary Master URL for this Topic
                        </span>
                        <div className="font-mono text-xs font-bold text-emerald-900 dark:text-emerald-100 break-all">
                          {cluster.primary_url}
                        </div>
                      </div>
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-emerald-600 text-white shadow-2xs">
                        Master Pillar
                      </span>
                    </div>

                    {/* Member Pages Table */}
                    <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-hidden overflow-x-auto text-xs">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-semibold border-b border-zinc-200 dark:border-zinc-800">
                            <th className="py-2.5 px-3">Role & Page URL</th>
                            <th className="py-2.5 px-3">Search Intent</th>
                            <th className="py-2.5 px-3">Recommended Action</th>
                            <th className="py-2.5 px-3">Target URL</th>
                            <th className="py-2.5 px-3 text-right">Words</th>
                            <th className="py-2.5 px-3 text-center">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                          {cluster.pages.map((p, pIdx) => {
                            const actionBadge = getActionBadge(p.action);

                            return (
                              <tr
                                key={pIdx}
                                className={`hover:bg-zinc-50 dark:hover:bg-zinc-800/40 transition ${
                                  p.role === "PRIMARY" ? "bg-emerald-50/30 dark:bg-emerald-950/10 font-medium" : ""
                                }`}
                              >
                                {/* Role & URL */}
                                <td className="py-3 px-3 align-top space-y-1">
                                  <div className="flex items-center gap-1.5">
                                    <span
                                      className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${
                                        p.role === "PRIMARY"
                                          ? "bg-emerald-200 text-emerald-900 dark:bg-emerald-900 dark:text-emerald-200"
                                          : "bg-zinc-200 text-zinc-700 dark:bg-zinc-700 dark:text-zinc-300"
                                      }`}
                                    >
                                      {p.role}
                                    </span>
                                    <a
                                      href={p.url}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="font-mono text-blue-600 dark:text-blue-400 hover:underline break-all truncate max-w-xs"
                                    >
                                      {p.url}
                                    </a>
                                  </div>
                                  <div className="text-[11px] text-zinc-600 dark:text-zinc-400 line-clamp-1">
                                    {p.title || "(No Title)"}
                                  </div>
                                </td>

                                {/* Search Intent */}
                                <td className="py-3 px-3 align-top">
                                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${getIntentBadge(p.search_intent)}`}>
                                    {p.search_intent}
                                  </span>
                                </td>

                                {/* Action */}
                                <td className="py-3 px-3 align-top">
                                  <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border inline-block ${actionBadge.cls}`}>
                                    {actionBadge.label}
                                  </span>
                                </td>

                                {/* Target URL */}
                                <td className="py-3 px-3 align-top font-mono text-[11px]">
                                  {p.target_url ? (
                                    <span className="text-emerald-600 dark:text-emerald-400 break-all truncate max-w-xs block">
                                      {p.target_url}
                                    </span>
                                  ) : (
                                    <span className="text-zinc-400 italic">None (Self)</span>
                                  )}
                                </td>

                                {/* Words */}
                                <td className="py-3 px-3 align-top text-right text-zinc-600 dark:text-zinc-400">
                                  {p.word_count}
                                </td>

                                {/* Status */}
                                <td className="py-3 px-3 align-top text-center text-zinc-600 dark:text-zinc-400">
                                  {p.status_code || "ERR"}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>

                    {/* Detailed Rationale for each page */}
                    <div className="space-y-2 pt-1">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-400">
                        Detailed Action Rationale & Evidence:
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                        {cluster.pages.map((p, pIdx) => (
                          <div
                            key={pIdx}
                            className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-700/80 space-y-1"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <span className="font-mono text-[11px] font-bold text-zinc-900 dark:text-white truncate max-w-[220px]">
                                {p.url}
                              </span>
                              <div className="flex items-center gap-1.5 shrink-0">
                                {p.topic_source === "USER_DEFINED" && p.topic_confidence ? (
                                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                                    {p.topic_confidence.toFixed(0)}% match
                                  </span>
                                ) : null}
                                <span className="text-[10px] font-semibold text-indigo-600 dark:text-indigo-400">
                                  {p.action_label}
                                </span>
                              </div>
                            </div>
                            <p className="text-[11px] text-zinc-600 dark:text-zinc-300 leading-relaxed">
                              {p.reason}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>

                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

    </div>
  );
}
