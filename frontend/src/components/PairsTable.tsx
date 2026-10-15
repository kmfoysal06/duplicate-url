"use client";

import React, { useState, useMemo } from "react";
import { EvaluatedPair } from "@/types/seo";
import { SearchIcon, ExternalLinkIcon, FileTextIcon } from "./Icons";

interface PairsTableProps {
  pairs: EvaluatedPair[];
  onOpenDiff: (pairId: string) => void;
}

export default function PairsTable({ pairs, onOpenDiff }: PairsTableProps) {
  const [filterClass, setFilterClass] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");

  const filteredPairs = useMemo(() => {
    return pairs
      .filter((p) => {
        if (filterClass !== "All" && p.classification !== filterClass) return false;
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchUrl = p.url1.toLowerCase().includes(q) || p.url2.toLowerCase().includes(q);
          const matchTitle = p.title1.toLowerCase().includes(q) || p.title2.toLowerCase().includes(q);
          if (!matchUrl && !matchTitle) return false;
        }
        return true;
      })
      .sort((a, b) => {
        if (sortOrder === "desc") {
          return b.similarity_score - a.similarity_score;
        } else {
          return a.similarity_score - b.similarity_score;
        }
      });
  }, [pairs, filterClass, searchQuery, sortOrder]);

  const getScoreBadge = (score: number, classification: string) => {
    let color = "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300";
    if (classification === "Exact content duplicate") {
      color = "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/50 dark:text-red-300 dark:border-red-900";
    } else if (classification === "Near duplicate") {
      color = "bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950/50 dark:text-orange-300 dark:border-orange-900";
    } else if (classification === "Potential duplicate") {
      color = "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/50 dark:text-amber-300 dark:border-amber-900";
    }

    return (
      <div className="flex flex-col items-start gap-1">
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${color}`}>
          {score.toFixed(1)}%
        </span>
        <span className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
          {classification}
        </span>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Controls: Search, Classification Filter, Sorting */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800">
        
        {/* Search */}
        <div className="relative flex-1 min-w-[240px]">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-400">
            <SearchIcon className="w-4 h-4" />
          </div>
          <input
            type="text"
            placeholder="Search by URL or title..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Classification Filter Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          {[
            { label: "All Pairs", value: "All" },
            { label: "Exact (100%)", value: "Exact content duplicate" },
            { label: "Near (85%+)", value: "Near duplicate" },
            { label: "Potential (70-84%)", value: "Potential duplicate" },
            { label: "Low (<70%)", value: "Low similarity" },
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => setFilterClass(tab.value)}
              className={`px-3 py-1 rounded-lg font-medium transition ${
                filterClass === tab.value
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "bg-white dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Sort Order Toggle */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500 dark:text-zinc-400">Sort:</span>
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as "desc" | "asc")}
            className="text-xs px-2.5 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200"
          >
            <option value="desc">Highest Similarity First</option>
            <option value="asc">Lowest Similarity First</option>
          </select>
        </div>

      </div>

      {/* Results Table */}
      <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-hidden bg-white dark:bg-zinc-900 shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-zinc-100 dark:bg-zinc-800/80 text-zinc-600 dark:text-zinc-300 font-semibold border-b border-zinc-200 dark:border-zinc-800">
                <th className="py-3 px-4 w-36">Similarity & Tier</th>
                <th className="py-3 px-4 w-1/3">URL 1 & Metadata</th>
                <th className="py-3 px-4 w-1/3">URL 2 & Metadata</th>
                <th className="py-3 px-4 min-w-[200px]">SEO Recommended Action</th>
                <th className="py-3 px-4 w-28 text-center">Comparison</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
              {filteredPairs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-zinc-400 dark:text-zinc-500">
                    No matching URL pairs found for current filters.
                  </td>
                </tr>
              ) : (
                filteredPairs.map((p) => (
                  <tr
                    key={p.pair_id}
                    className="hover:bg-zinc-50/80 dark:hover:bg-zinc-800/40 transition group"
                  >
                    {/* Score & Tier */}
                    <td className="py-3.5 px-4 align-top">
                      {getScoreBadge(p.similarity_score, p.classification)}
                    </td>

                    {/* Page 1 Details */}
                    <td className="py-3.5 px-4 align-top space-y-1">
                      <a
                        href={p.url1}
                        target="_blank"
                        rel="noreferrer"
                        className="font-mono text-blue-600 dark:text-blue-400 hover:underline break-all flex items-center gap-1 font-medium"
                      >
                        <span className="truncate max-w-xs">{p.url1}</span>
                        <ExternalLinkIcon className="w-3 h-3 shrink-0 opacity-60" />
                      </a>

                      <p className="text-zinc-800 dark:text-zinc-200 font-medium line-clamp-1">
                        {p.title1 || "(No Title)"}
                      </p>

                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-zinc-500 dark:text-zinc-400">
                        <span className="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700">
                          Status: {p.status_code1 || "ERR"}
                        </span>
                        <span>{p.word_count1} words</span>
                        {p.canonical1 ? (
                          <span
                            className="font-mono truncate max-w-[180px] text-zinc-600 dark:text-zinc-400"
                            title={`Canonical: ${p.canonical1}`}
                          >
                            rel: {p.canonical1}
                          </span>
                        ) : (
                          <span className="text-amber-600 dark:text-amber-400 font-medium">No canonical tag</span>
                        )}
                      </div>
                    </td>

                    {/* Page 2 Details */}
                    <td className="py-3.5 px-4 align-top space-y-1">
                      <a
                        href={p.url2}
                        target="_blank"
                        rel="noreferrer"
                        className="font-mono text-emerald-600 dark:text-emerald-400 hover:underline break-all flex items-center gap-1 font-medium"
                      >
                        <span className="truncate max-w-xs">{p.url2}</span>
                        <ExternalLinkIcon className="w-3 h-3 shrink-0 opacity-60" />
                      </a>

                      <p className="text-zinc-800 dark:text-zinc-200 font-medium line-clamp-1">
                        {p.title2 || "(No Title)"}
                      </p>

                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-zinc-500 dark:text-zinc-400">
                        <span className="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700">
                          Status: {p.status_code2 || "ERR"}
                        </span>
                        <span>{p.word_count2} words</span>
                        {p.canonical2 ? (
                          <span
                            className="font-mono truncate max-w-[180px] text-zinc-600 dark:text-zinc-400"
                            title={`Canonical: ${p.canonical2}`}
                          >
                            rel: {p.canonical2}
                          </span>
                        ) : (
                          <span className="text-amber-600 dark:text-amber-400 font-medium">No canonical tag</span>
                        )}
                      </div>
                    </td>

                    {/* SEO Recommended Action */}
                    <td className="py-3.5 px-4 align-top">
                      <div className="p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 text-[11px] leading-relaxed text-zinc-700 dark:text-zinc-300">
                        {p.same_canonical && (
                          <span className="inline-block px-1.5 py-0.5 mb-1 mr-1 text-[10px] font-bold rounded bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                            Same Canonical Tag
                          </span>
                        )}
                        {p.title_match && (
                          <span className="inline-block px-1.5 py-0.5 mb-1 mr-1 text-[10px] font-bold rounded bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                            Identical Title
                          </span>
                        )}
                        <div>{p.recommended_action}</div>
                      </div>
                    </td>

                    {/* Diff Button */}
                    <td className="py-3.5 px-4 align-middle text-center">
                      <button
                        onClick={() => onOpenDiff(p.pair_id)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-900 hover:bg-indigo-600 hover:text-white dark:hover:bg-indigo-600 dark:hover:text-white transition shadow-2xs"
                      >
                        <FileTextIcon className="w-3.5 h-3.5" />
                        Diff
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Table Footer with Count */}
      <div className="text-xs text-zinc-500 dark:text-zinc-400 text-right">
        Showing {filteredPairs.length} of {pairs.length} evaluated URL pairs
      </div>
    </div>
  );
}
