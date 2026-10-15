"use client";

import React, { useState } from "react";
import { DuplicateCluster, EvaluatedPair, CrawledPage } from "@/types/seo";
import { LayersIcon, ExternalLinkIcon, FileTextIcon } from "./Icons";

interface ClusterViewProps {
  clusters: DuplicateCluster[];
  pairs: EvaluatedPair[];
  pages: CrawledPage[];
  onOpenDiff: (pairId: string) => void;
}

export default function ClusterView({ clusters, pairs, pages, onOpenDiff }: ClusterViewProps) {
  const [expandedCluster, setExpandedCluster] = useState<string | null>(
    clusters.length > 0 ? clusters[0].cluster_id : null
  );

  const pagesMap = React.useMemo(() => {
    const map = new Map<string, CrawledPage>();
    pages.forEach((p) => map.set(p.original_url, p));
    return map;
  }, [pages]);

  const getClusterBadge = (highestClass: string) => {
    if (highestClass === "Exact content duplicate") {
      return "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/60 dark:text-red-300 dark:border-red-900";
    }
    if (highestClass === "Near duplicate") {
      return "bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950/60 dark:text-orange-300 dark:border-orange-900";
    }
    return "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-900";
  };

  if (clusters.length === 0) {
    return (
      <div className="p-12 text-center rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        <p className="text-zinc-500 dark:text-zinc-400 text-sm">
          No duplicate clusters detected. All crawled pages appear sufficiently unique!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {clusters.map((cluster) => {
        const isExpanded = expandedCluster === cluster.cluster_id;
        const clusterPairs = pairs.filter(
          (p) =>
            cluster.members.includes(p.url1) &&
            cluster.members.includes(p.url2) &&
            p.similarity_score >= 70.0
        );

        return (
          <div
            key={cluster.cluster_id}
            className="border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 overflow-hidden shadow-2xs"
          >
            {/* Cluster Header Banner */}
            <div
              onClick={() => setExpandedCluster(isExpanded ? null : cluster.cluster_id)}
              className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800/40 transition select-none"
            >
              <div className="flex items-center gap-3">
                <span className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
                  <LayersIcon className="w-5 h-5" />
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                      {cluster.cluster_id}
                    </h3>
                    <span
                      className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${getClusterBadge(
                        cluster.highest_classification
                      )}`}
                    >
                      {cluster.highest_classification} (Up to {cluster.highest_similarity.toFixed(1)}%)
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                    Cluster contains <strong className="text-zinc-700 dark:text-zinc-300">{cluster.member_count} interconnected URLs</strong> across {clusterPairs.length} duplicate pairings.
                  </p>
                </div>
              </div>

              <div className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold flex items-center gap-1">
                {isExpanded ? "Collapse" : "Expand Cluster"}
              </div>
            </div>

            {/* Expanded Cluster Details */}
            {isExpanded && (
              <div className="px-5 pb-5 pt-2 border-t border-zinc-100 dark:border-zinc-800/80 space-y-5">
                
                {/* Member URLs List */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-2.5">
                    Pages in this Duplicate Group ({cluster.members.length})
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {cluster.members.map((url, idx) => {
                      const page = pagesMap.get(url);
                      return (
                        <div
                          key={idx}
                          className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200/80 dark:border-zinc-700/80 space-y-1 text-xs"
                        >
                          <a
                            href={url}
                            target="_blank"
                            rel="noreferrer"
                            className="font-mono font-medium text-blue-600 dark:text-blue-400 hover:underline break-all flex items-center gap-1"
                          >
                            <span className="truncate max-w-sm">{url}</span>
                            <ExternalLinkIcon className="w-3 h-3 shrink-0 opacity-60" />
                          </a>

                          <div className="text-zinc-800 dark:text-zinc-200 font-medium line-clamp-1">
                            {page?.title || "(No Page Title)"}
                          </div>

                          <div className="flex flex-wrap items-center gap-2 text-[11px] text-zinc-500 dark:text-zinc-400 pt-0.5">
                            <span className="px-1.5 py-0.2 rounded bg-zinc-200 dark:bg-zinc-700 text-zinc-800 dark:text-zinc-200">
                              Status: {page?.status_code || "ERR"}
                            </span>
                            <span>{page?.word_count || 0} words</span>
                            {page?.canonical_url ? (
                              <span className="truncate max-w-[200px] text-emerald-600 dark:text-emerald-400 font-mono">
                                canonical: {page.canonical_url}
                              </span>
                            ) : (
                              <span className="text-amber-600 dark:text-amber-400">Missing canonical</span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Evaluated Pair Combinations in Cluster */}
                {clusterPairs.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-2.5">
                      Pairwise Overlap & Recommendations ({clusterPairs.length})
                    </h4>
                    <div className="divide-y divide-zinc-200 dark:divide-zinc-800 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden">
                      {clusterPairs.map((pair) => (
                        <div
                          key={pair.pair_id}
                          className="p-3.5 bg-white dark:bg-zinc-900/60 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
                        >
                          <div className="space-y-1 flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-zinc-900 dark:text-white">
                                {pair.similarity_score.toFixed(1)}% Similarity
                              </span>
                              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300">
                                {pair.classification}
                              </span>
                            </div>

                            <div className="font-mono text-[11px] text-zinc-600 dark:text-zinc-400 break-all">
                              <span className="text-blue-600 dark:text-blue-400">{pair.url1}</span>
                              <span className="mx-2 text-zinc-400">↔</span>
                              <span className="text-emerald-600 dark:text-emerald-400">{pair.url2}</span>
                            </div>

                            <p className="text-zinc-700 dark:text-zinc-300 text-[11px] pt-1">
                              <strong>SEO Action: </strong>
                              {pair.recommended_action}
                            </p>
                          </div>

                          <button
                            onClick={() => onOpenDiff(pair.pair_id)}
                            className="self-start md:self-center shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-900 hover:bg-indigo-600 hover:text-white transition flex items-center gap-1.5"
                          >
                            <FileTextIcon className="w-3.5 h-3.5" />
                            View Side-by-Side Diff
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
