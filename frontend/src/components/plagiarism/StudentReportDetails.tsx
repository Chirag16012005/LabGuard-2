"use client";

import { useMemo } from "react";
import { X } from "lucide-react";

type Comparison = {
  document_id: string;
  similarity: number;
  matched_passages: number;
};

type RiskTone = "green" | "yellow" | "red";

const toneClasses: Record<RiskTone, { badge: string; text: string; filled: string }> = {
  green: {
    badge:
      "bg-emerald-100 text-emerald-700 border border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800",
    text: "text-emerald-600 dark:text-emerald-300",
    filled: "bg-emerald-500",
  },
  yellow: {
    badge:
      "bg-amber-100 text-amber-700 border border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800",
    text: "text-amber-600 dark:text-amber-300",
    filled: "bg-amber-500",
  },
  red: {
    badge:
      "bg-rose-100 text-rose-700 border border-rose-200 dark:bg-rose-900/30 dark:text-rose-300 dark:border-rose-800",
    text: "text-rose-600 dark:text-rose-300",
    filled: "bg-rose-500",
  },
};

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === "object" && value !== null;
};

const normalizePercent = (value: unknown): number => {
  const num = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(num)) return 0;
  const percent = num <= 1 ? num * 100 : num;
  return Math.max(0, Math.min(100, percent));
};

const getTone = (score: number): RiskTone => {
  if (score < 40) return "green";
  if (score <= 70) return "yellow";
  return "red";
};

type ParsedStudentReport = {
  student_report_id: string;
  plagiarism_score: number;
  comparisons: Comparison[];
};

const parseStudentReport = (raw: unknown, fallbackId?: string | null): ParsedStudentReport | null => {
  if (!isRecord(raw)) return null;

  const student_report_id = String(raw.student_report_id ?? fallbackId ?? "").trim();
  const plagiarism_score = normalizePercent(raw.plagiarism_score);

  const comparisonsRaw = Array.isArray(raw.comparisons) ? raw.comparisons : [];
  const comparisons: Comparison[] = comparisonsRaw
    .map((cmp) => {
      if (!isRecord(cmp)) return null;
      return {
        document_id: String(cmp.document_id ?? "Unknown"),
        similarity: normalizePercent(cmp.similarity),
        matched_passages: Number(cmp.matched_passages ?? 0),
      };
    })
    .filter((cmp): cmp is Comparison => cmp !== null)
    .sort((a, b) => b.similarity - a.similarity);

  if (!student_report_id) return null;
  return { student_report_id, plagiarism_score, comparisons };
};

function SegmentedBar({ score }: { score: number }) {
  const tone = getTone(score);
  const filled = Math.max(0, Math.min(10, Math.round(score / 10)));

  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: 10 }).map((_, index) => (
        <span
          key={index}
          className={`h-2 flex-1 rounded-full ${
            index < filled ? toneClasses[tone].filled : "bg-slate-200 dark:bg-slate-700"
          }`}
        />
      ))}
    </div>
  );
}

export function StudentReportDetails({
  open,
  studentReport,
  studentReportId,
  isLoading,
  isError,
  onCloseAction,
}: {
  open: boolean;
  studentReport: unknown;
  studentReportId?: string | null;
  isLoading?: boolean;
  isError?: boolean;
  onCloseAction: () => void;
}) {
  const parsed = useMemo(() => parseStudentReport(studentReport, studentReportId), [studentReport, studentReportId]);

  const mostSimilar = useMemo(() => {
    if (!parsed || parsed.comparisons.length === 0) return null;
    return parsed.comparisons[0];
  }, [parsed]);

  const score = parsed?.plagiarism_score ?? 0;
  const tone = getTone(score);

  return (
    <div
      className={`fixed inset-0 z-50 transition-opacity duration-300 ${
        open ? "opacity-100" : "pointer-events-none opacity-0"
      }`}
      aria-hidden={!open}
    >
      <button
        type="button"
        aria-label="Close student report"
        onClick={onCloseAction}
        className="absolute inset-0 cursor-default bg-slate-900/40 backdrop-blur-sm"
      />

      <aside
        className={
          `absolute right-0 top-0 h-full w-full max-w-xl transform border-l border-slate-200 bg-white shadow-xl transition-transform duration-300 dark:border-slate-800 dark:bg-slate-950 ${
            open ? "translate-x-0" : "translate-x-full"
          }`
        }
        role="dialog"
        aria-modal="true"
      >
        <div className="flex h-full flex-col">
          <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-6 py-5 dark:border-slate-800">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">Student Report</p>
              <h3 className="mt-1 truncate text-lg font-semibold text-slate-900 dark:text-white">
                {parsed?.student_report_id ?? studentReportId ?? "Student report"}
              </h3>
            </div>

            <button
              type="button"
              onClick={onCloseAction}
              className="rounded-full border border-slate-200 bg-white p-2 text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200 dark:hover:bg-slate-900"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-6">
            {isLoading ? (
              <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-slate-600 dark:border-slate-700 dark:border-t-slate-200" />
                <p className="text-sm text-slate-600 dark:text-slate-300">Loading student report…</p>
              </div>
            ) : isError ? (
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <p className="text-sm font-semibold text-slate-900 dark:text-white">Couldn’t load this report.</p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Try again in a moment.</p>
              </div>
            ) : !parsed ? (
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <p className="text-sm text-slate-600 dark:text-slate-300">No report data available.</p>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-medium text-slate-600 dark:text-slate-300">Plagiarism score</p>
                      <p className="mt-2 text-4xl font-semibold text-slate-900 dark:text-white">
                        {score.toFixed(1)}%
                      </p>
                    </div>
                    <span className={`mt-1 rounded-full px-3 py-1 text-xs font-semibold ${toneClasses[tone].badge}`}>
                      {tone === "green" ? "Low risk" : tone === "yellow" ? "Medium risk" : "High risk"}
                    </span>
                  </div>

                  <div className="mt-4">
                    <SegmentedBar score={score} />
                  </div>

                  {mostSimilar ? (
                    <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50/60 p-4 dark:border-slate-700 dark:bg-slate-800/40">
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        Most Similar Document
                      </p>
                      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">
                        {mostSimilar.document_id}
                      </p>
                      <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                        Similarity: <span className={`font-semibold ${toneClasses[getTone(mostSimilar.similarity)].text}`}>
                          {mostSimilar.similarity.toFixed(1)}%
                        </span>
                        {" • "}Matches: <span className="font-semibold">{mostSimilar.matched_passages}</span>
                      </p>
                    </div>
                  ) : null}
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
                  <div className="border-b border-slate-200 px-6 py-4 dark:border-slate-800">
                    <h4 className="text-sm font-semibold text-slate-900 dark:text-white">Comparisons</h4>
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                      Documents compared against this submission.
                    </p>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
                        <tr className="text-left text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                          <th className="px-6 py-3 font-semibold">Compared Document</th>
                          <th className="px-6 py-3 font-semibold">Similarity</th>
                          <th className="px-6 py-3 font-semibold">Matches</th>
                        </tr>
                      </thead>
                      <tbody>
                        {parsed.comparisons.length === 0 ? (
                          <tr>
                            <td colSpan={3} className="px-6 py-6 text-center text-slate-500 dark:text-slate-400">
                              No comparisons available.
                            </td>
                          </tr>
                        ) : (
                          parsed.comparisons.map((comparison, index) => {
                            const similarityTone = getTone(comparison.similarity);
                            const isTop = index === 0;

                            return (
                              <tr
                                key={`${parsed.student_report_id}-${comparison.document_id}`}
                                className={
                                  isTop
                                    ? "bg-amber-50/80 dark:bg-amber-950/20"
                                    : "hover:bg-slate-50 dark:hover:bg-slate-800/50"
                                }
                              >
                                <td className="px-6 py-3 font-medium text-slate-800 dark:text-slate-200">
                                  {comparison.document_id}
                                </td>
                                <td className="px-6 py-3">
                                  <span className={`font-semibold ${toneClasses[similarityTone].text}`}>
                                    {comparison.similarity.toFixed(1)}%
                                  </span>
                                </td>
                                <td className="px-6 py-3 text-slate-600 dark:text-slate-300">
                                  {comparison.matched_passages}
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </aside>
    </div>
  );
}
