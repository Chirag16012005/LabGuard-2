"use client";

import { Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import type { StudentReportEntry } from "@/features/student/api";

interface StudentReportViewProps {
  report: StudentReportEntry | undefined;
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
}

const getSimilarityColor = (score: number): string => {
  if (score >= 0.8) return "text-red-600 bg-red-50";
  if (score >= 0.6) return "text-orange-600 bg-orange-50";
  if (score >= 0.4) return "text-yellow-600 bg-yellow-50";
  if (score >= 0.2) return "text-blue-600 bg-blue-50";
  return "text-green-600 bg-green-50";
};

const getSimilarityBadgeColor = (score: number): string => {
  if (score >= 0.8) return "bg-red-100 text-red-800";
  if (score >= 0.6) return "bg-orange-100 text-orange-800";
  if (score >= 0.4) return "bg-yellow-100 text-yellow-800";
  if (score >= 0.2) return "bg-blue-100 text-blue-800";
  return "bg-green-100 text-green-800";
};

export function StudentReportView({
  report,
  isLoading,
  isError,
  error,
}: StudentReportViewProps) {
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-12 shadow-sm flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
        <span className="ml-3 text-slate-500">Loading your plagiarism report...</span>
      </div>
    );
  }

  if (isError || !report) {
    const is404 = error?.message?.includes?.("404");
    return (
      <div
        className={`rounded-2xl p-8 border flex items-start gap-4 ${
          is404
            ? "bg-blue-50 border-blue-200 dark:bg-blue-900/10 dark:border-blue-800/40"
            : "bg-red-50 border-red-200 dark:bg-red-900/10 dark:border-red-800/40"
        }`}
      >
        <AlertCircle
          className={`h-6 w-6 mt-1 flex-shrink-0 ${
            is404 ? "text-blue-600" : "text-red-600"
          }`}
        />
        <div>
          <h3 className={`font-semibold ${is404 ? "text-blue-900 dark:text-blue-200" : "text-red-900 dark:text-red-200"}`}>
            {is404 ? "Report Not Released" : "Error Loading Report"}
          </h3>
          <p className={`text-sm mt-1 ${is404 ? "text-blue-700 dark:text-blue-300" : "text-red-700 dark:text-red-300"}`}>
            {is404
              ? "Your plagiarism report has not been released by your instructor yet. Check back later."
              : error?.message || "Failed to load your plagiarism report. Please try again."}
          </p>
        </div>
      </div>
    );
  }

  const plagiarismScore = report.plagiarism_score ?? 0;
  const comparisons = Array.isArray(report.comparisons) ? report.comparisons : [];

  return (
    <div className="space-y-6">
      {/* Plagiarism Score Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400 mb-2">
              Overall Plagiarism Score
            </h3>
            <div className={`inline-block px-6 py-3 rounded-xl font-bold text-3xl ${getSimilarityColor(plagiarismScore)}`}>
              {(plagiarismScore * 100).toFixed(1)}%
            </div>
          </div>
          <div className={`text-sm font-medium px-4 py-2 rounded-lg ${getSimilarityBadgeColor(plagiarismScore)}`}>
            {plagiarismScore >= 0.8
              ? "High Similarity"
              : plagiarismScore >= 0.6
                ? "Medium-High Similarity"
                : plagiarismScore >= 0.4
                  ? "Moderate Similarity"
                  : plagiarismScore >= 0.2
                    ? "Low Similarity"
                    : "Very Low Similarity"}
          </div>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-4">
          {plagiarismScore < 0.1
            ? "Your work appears to be original."
            : plagiarismScore < 0.3
              ? "Your work shows minimal overlap with existing sources."
              : "Your work contains significant overlap with compared submissions."}
        </p>
      </div>

      {/* Comparisons Table */}
      {comparisons.length > 0 ? (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">
            <h3 className="font-semibold text-slate-900 dark:text-white">
              Similarity Comparisons ({comparisons.length})
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                  <th className="px-6 py-3 text-left font-semibold text-slate-700 dark:text-slate-300">
                    Document
                  </th>
                  <th className="px-6 py-3 text-left font-semibold text-slate-700 dark:text-slate-300">
                    Similarity
                  </th>
                  <th className="px-6 py-3 text-left font-semibold text-slate-700 dark:text-slate-300">
                    Matched Passages
                  </th>
                </tr>
              </thead>
              <tbody>
                {comparisons.map((comp, idx) => {
                  const docId =
                    typeof comp === "object" && comp !== null
                      ? (comp as Record<string, unknown>).document_id
                      : "";
                  const similarity =
                    typeof comp === "object" && comp !== null
                      ? ((comp as Record<string, unknown>).similarity as number) ?? 0
                      : 0;
                  const passages =
                    typeof comp === "object" && comp !== null
                      ? ((comp as Record<string, unknown>).passages as number) ?? 0
                      : 0;

                  return (
                    <tr
                      key={idx}
                      className="border-b border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors"
                    >
                      <td className="px-6 py-4 text-slate-900 dark:text-slate-100">
                        {String(docId || `Document ${idx + 1}`)}
                      </td>
                      <td className="px-6 py-4">
                        <div className={`inline-block px-3 py-1 rounded-full font-semibold text-sm ${getSimilarityBadgeColor(similarity)}`}>
                          {(similarity * 100).toFixed(1)}%
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-600 dark:text-slate-400">
                        {passages} {passages === 1 ? "passage" : "passages"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 shadow-sm text-center">
          <CheckCircle2 className="h-12 w-12 mx-auto text-green-500 mb-3" />
          <p className="text-slate-600 dark:text-slate-400 font-medium">
            No significant similarities detected in your submission.
          </p>
        </div>
      )}
    </div>
  );
}
