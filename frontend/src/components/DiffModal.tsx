"use client";

import React, { useState, useEffect } from "react";
import { DetailedPairDiff } from "@/types/seo";
import { XIcon, AlertTriangleIcon, FileTextIcon } from "./Icons";

interface DiffModalProps {
  jobId: string;
  pairId: string;
  onClose: () => void;
}

export default function DiffModal({ jobId, pairId, onClose }: DiffModalProps) {
  const [loading, setLoading] = useState<boolean>(true);
  const [diffData, setDiffData] = useState<DetailedPairDiff | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"side-by-side" | "breakdown">("side-by-side");

  useEffect(() => {
    async function fetchDiff() {
      setLoading(true);
      setError(null);
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
        const res = await fetch(`${apiBase}/api/jobs/${jobId}/diff?pair_id=${encodeURIComponent(pairId)}`);
        if (!res.ok) {
          throw new Error(`Failed to load comparison: ${res.statusText}`);
        }
        const data = await res.json();
        setDiffData(data);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to load diff";
        setError(message);
      } finally {
        setLoading(false);
      }
    }
    fetchDiff();
  }, [jobId, pairId]);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const getScoreBadgeClass = (score: number) => {
    if (score >= 100) return "bg-red-100 text-red-800 border-red-200 dark:bg-red-950/60 dark:text-red-300";
    if (score >= 85) return "bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-950/60 dark:text-orange-300";
    if (score >= 70) return "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-950/60 dark:text-amber-300";
    return "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300";
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-xs">
      <div className="relative w-full max-w-6xl max-h-[92vh] flex flex-col bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-800 overflow-hidden">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/80">
          <div className="flex items-center gap-3">
            <span className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
              <FileTextIcon className="w-5 h-5" />
            </span>
            <div>
              <h2 className="text-lg font-bold text-zinc-900 dark:text-white">
                Side-by-Side Content Comparison
              </h2>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Detailed diff of text, headings, and canonical directives
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {diffData && (
              <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getScoreBadgeClass(diffData.similarity_score)}`}>
                {diffData.similarity_score.toFixed(1)}% Similarity • {diffData.classification}
              </span>
            )}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-800 dark:hover:text-white transition"
              aria-label="Close modal"
            >
              <XIcon className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading && (
            <div className="flex flex-col items-center justify-center py-20 text-zinc-500">
              <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-3"></div>
              <p className="text-sm">Comparing page content and computing diff...</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-900 text-sm">
              {error}
            </div>
          )}

          {diffData && (
            <>
              {/* SEO Action Recommendation Box */}
              <div className="p-4 rounded-xl bg-indigo-50/80 dark:bg-indigo-950/40 border border-indigo-200/80 dark:border-indigo-900/60">
                <div className="flex items-start gap-3">
                  <div className="p-1.5 rounded-md bg-indigo-600 text-white shrink-0 mt-0.5">
                    <AlertTriangleIcon className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-900 dark:text-indigo-300">
                      SEO Recommendation
                    </h4>
                    <p className="text-sm text-indigo-950 dark:text-indigo-200 mt-0.5 font-medium leading-relaxed">
                      {diffData.recommended_action}
                    </p>
                  </div>
                </div>
              </div>

              {/* Side-by-Side Metadata Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Page 1 Metadata */}
                <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-200 dark:border-zinc-800">
                  <div className="flex items-center justify-between pb-2 mb-3 border-b border-zinc-200 dark:border-zinc-700">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                      <span className="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">Page 1</span>
                    </div>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-300">
                      Status: {diffData.status_code1 || "Error"} • {diffData.word_count1} words
                    </span>
                  </div>

                  <p className="text-xs font-mono text-blue-600 dark:text-blue-400 break-all mb-3 font-semibold">
                    {diffData.url1}
                  </p>

                  <div className="space-y-2 text-xs">
                    <div>
                      <span className="text-zinc-400 dark:text-zinc-500 font-semibold">Title: </span>
                      <span className="text-zinc-800 dark:text-zinc-200 font-medium">{diffData.title1 || "(None)"}</span>
                    </div>
                    <div>
                      <span className="text-zinc-400 dark:text-zinc-500 font-semibold">Canonical: </span>
                      <span className="font-mono text-zinc-700 dark:text-zinc-300 break-all">
                        {diffData.canonical1 || "(Missing canonical tag)"}
                      </span>
                    </div>
                    <div>
                      <span className="text-zinc-400 dark:text-zinc-500 font-semibold">H1 Headings: </span>
                      <span className="text-zinc-700 dark:text-zinc-300">
                        {diffData.h1_1.length > 0 ? diffData.h1_1.join(" • ") : "(None)"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Page 2 Metadata */}
                <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-200 dark:border-zinc-800">
                  <div className="flex items-center justify-between pb-2 mb-3 border-b border-zinc-200 dark:border-zinc-700">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                      <span className="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">Page 2</span>
                    </div>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-300">
                      Status: {diffData.status_code2 || "Error"} • {diffData.word_count2} words
                    </span>
                  </div>

                  <p className="text-xs font-mono text-emerald-600 dark:text-emerald-400 break-all mb-3 font-semibold">
                    {diffData.url2}
                  </p>

                  <div className="space-y-2 text-xs">
                    <div>
                      <span className="text-zinc-400 dark:text-zinc-500 font-semibold">Title: </span>
                      <span className="text-zinc-800 dark:text-zinc-200 font-medium">{diffData.title2 || "(None)"}</span>
                    </div>
                    <div>
                      <span className="text-zinc-400 dark:text-zinc-500 font-semibold">Canonical: </span>
                      <span className="font-mono text-zinc-700 dark:text-zinc-300 break-all">
                        {diffData.canonical2 || "(Missing canonical tag)"}
                      </span>
                    </div>
                    <div>
                      <span className="text-zinc-400 dark:text-zinc-500 font-semibold">H1 Headings: </span>
                      <span className="text-zinc-700 dark:text-zinc-300">
                        {diffData.h1_2.length > 0 ? diffData.h1_2.join(" • ") : "(None)"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* View Switcher Tabs */}
              <div className="flex items-center justify-between border-b border-zinc-200 dark:border-zinc-800 pt-2">
                <div className="flex gap-2">
                  <button
                    onClick={() => setActiveTab("side-by-side")}
                    className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition ${
                      activeTab === "side-by-side"
                        ? "border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400"
                        : "border-transparent text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300"
                    }`}
                  >
                    Inline Word Diff
                  </button>
                  <button
                    onClick={() => setActiveTab("breakdown")}
                    className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition ${
                      activeTab === "breakdown"
                        ? "border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400"
                        : "border-transparent text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300"
                    }`}
                  >
                    Shared vs. Unique Content Blocks
                  </button>
                </div>
                <div className="text-[11px] text-zinc-400 pb-2">
                  {diffData.shared_content.length} shared blocks • {diffData.unique_to_page1.length} unique P1 • {diffData.unique_to_page2.length} unique P2
                </div>
              </div>

              {/* Content Panel */}
              {activeTab === "side-by-side" ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Page 1 Token Diff */}
                  <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 font-sans text-xs leading-relaxed max-h-96 overflow-y-auto">
                    <div className="text-[11px] font-bold text-zinc-400 mb-2 uppercase">Page 1 Main Text</div>
                    <div className="flex flex-wrap gap-x-1 gap-y-0.5">
                      {diffData.diff_tokens_p1.map((tok, i) => (
                        <span
                          key={i}
                          className={
                            tok.type === "removed"
                              ? "bg-red-100 text-red-900 dark:bg-red-950/80 dark:text-red-200 px-0.5 rounded font-medium"
                              : "text-zinc-700 dark:text-zinc-300"
                          }
                        >
                          {tok.text}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Page 2 Token Diff */}
                  <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 font-sans text-xs leading-relaxed max-h-96 overflow-y-auto">
                    <div className="text-[11px] font-bold text-zinc-400 mb-2 uppercase">Page 2 Main Text</div>
                    <div className="flex flex-wrap gap-x-1 gap-y-0.5">
                      {diffData.diff_tokens_p2.map((tok, i) => (
                        <span
                          key={i}
                          className={
                            tok.type === "added"
                              ? "bg-emerald-100 text-emerald-900 dark:bg-emerald-950/80 dark:text-emerald-200 px-0.5 rounded font-medium"
                              : "text-zinc-700 dark:text-zinc-300"
                          }
                        >
                          {tok.text}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Shared Content */}
                  <div className="p-4 rounded-xl bg-blue-50/50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900/40">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                      <h4 className="text-xs font-bold text-blue-900 dark:text-blue-300 uppercase tracking-wider">
                        Shared Content Blocks ({diffData.shared_content.length})
                      </h4>
                    </div>
                    {diffData.shared_content.length === 0 ? (
                      <p className="text-xs text-zinc-400 italic">No identical sentence blocks found.</p>
                    ) : (
                      <div className="space-y-1.5 max-h-48 overflow-y-auto text-xs text-zinc-700 dark:text-zinc-300">
                        {diffData.shared_content.map((chunk, idx) => (
                          <div key={idx} className="p-2 rounded bg-white dark:bg-zinc-900/60 border border-blue-100 dark:border-blue-950">
                            {chunk}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Unique Blocks Side-by-Side */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Unique to P1 */}
                    <div className="p-4 rounded-xl bg-red-50/40 dark:bg-red-950/20 border border-red-200 dark:border-red-900/40">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-2 h-2 rounded-full bg-red-500"></span>
                        <h4 className="text-xs font-bold text-red-900 dark:text-red-300 uppercase tracking-wider">
                          Content Unique to Page 1 ({diffData.unique_to_page1.length})
                        </h4>
                      </div>
                      {diffData.unique_to_page1.length === 0 ? (
                        <p className="text-xs text-zinc-400 italic">No unique sentences (100% duplicate of Page 2).</p>
                      ) : (
                        <div className="space-y-1.5 max-h-48 overflow-y-auto text-xs text-zinc-700 dark:text-zinc-300">
                          {diffData.unique_to_page1.map((chunk, idx) => (
                            <div key={idx} className="p-2 rounded bg-white dark:bg-zinc-900/60 border border-red-100 dark:border-red-950">
                              {chunk}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Unique to P2 */}
                    <div className="p-4 rounded-xl bg-emerald-50/40 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/40">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                        <h4 className="text-xs font-bold text-emerald-900 dark:text-emerald-300 uppercase tracking-wider">
                          Content Unique to Page 2 ({diffData.unique_to_page2.length})
                        </h4>
                      </div>
                      {diffData.unique_to_page2.length === 0 ? (
                        <p className="text-xs text-zinc-400 italic">No unique sentences (100% duplicate of Page 1).</p>
                      ) : (
                        <div className="space-y-1.5 max-h-48 overflow-y-auto text-xs text-zinc-700 dark:text-zinc-300">
                          {diffData.unique_to_page2.map((chunk, idx) => (
                            <div key={idx} className="p-2 rounded bg-white dark:bg-zinc-900/60 border border-emerald-100 dark:border-emerald-950">
                              {chunk}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-end px-6 py-3 border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/80">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs font-semibold bg-zinc-200 hover:bg-zinc-300 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 transition"
          >
            Close Comparison
          </button>
        </div>

      </div>
    </div>
  );
}
