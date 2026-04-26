"use client";

import { useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { AlertCircle, ArrowLeft, Loader2, ShieldCheck } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { useAssignment } from "@/features/teacher/api";
import {
  useAssignmentReports,
  useAssignmentSubmissions,
  useStudentReport,
} from "@/features/student/api";

type ComparisonRow = {
  documentId: string;
  similarity: number;
  matchedPassages: number;
};

function scoreTone(score: number): {
  text: string;
  bg: string;
  chip: string;
  label: string;
} {
  if (score > 0.8) {
    return {
      text: "text-red-700 dark:text-red-300",
      bg: "bg-red-50 dark:bg-red-950/30",
      chip: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
      label: "High similarity",
    };
  }

  if (score >= 0.4) {
    return {
      text: "text-amber-700 dark:text-amber-300",
      bg: "bg-amber-50 dark:bg-amber-950/30",
      chip: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
      label: "Moderate similarity",
    };
  }

  return {
    text: "text-emerald-700 dark:text-emerald-300",
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
    chip: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
    label: "Low similarity",
  };
}

function LoadingState() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-center rounded-2xl border border-slate-200 bg-white p-8 dark:border-slate-800 dark:bg-slate-900">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
        <span className="ml-3 text-sm text-slate-500">Loading your report...</span>
      </div>

      <div className="animate-pulse rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
        <div className="h-3 w-40 rounded bg-slate-200 dark:bg-slate-700" />
        <div className="mt-4 h-10 w-32 rounded bg-slate-200 dark:bg-slate-700" />
        <div className="mt-4 h-3 w-56 rounded bg-slate-200 dark:bg-slate-700" />
      </div>

      <div className="animate-pulse rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
        <div className="h-4 w-44 rounded bg-slate-200 dark:bg-slate-700" />
        <div className="mt-5 space-y-3">
          <div className="h-14 rounded bg-slate-100 dark:bg-slate-800" />
          <div className="h-14 rounded bg-slate-100 dark:bg-slate-800" />
          <div className="h-14 rounded bg-slate-100 dark:bg-slate-800" />
        </div>
      </div>
    </div>
  );
}

export default function StudentAssignmentReportPage() {
  const { assignmentId } = useParams() as { assignmentId: string };
  const router = useRouter();

  const user = useAuthStore((s) => s.user);
  const hydrated = useAuthStore((s) => s.hydrated);

  const { data: assignment } = useAssignment(assignmentId);
  const { data: reports, isLoading: loadingReports } = useAssignmentReports(assignmentId);
  const { data: submissions, isLoading: loadingSubmissions } = useAssignmentSubmissions(assignmentId);

  const latestReport = useMemo(() => {
    return [...(reports ?? [])].sort((a, b) => {
      const aTime = a.generated_at ? Date.parse(a.generated_at) : 0;
      const bTime = b.generated_at ? Date.parse(b.generated_at) : 0;
      return (Number.isFinite(bTime) ? bTime : 0) - (Number.isFinite(aTime) ? aTime : 0);
    })[0] ?? null;
  }, [reports]);

  const mySubmission = useMemo(() => {
    if (!submissions || !user?.id) return null;
    return submissions.find((s) => s.studentId === user.id && Boolean(s.documentId)) ?? null;
  }, [submissions, user]);

  const studentReportId = useMemo(() => {
    if (!latestReport || !mySubmission?.documentId) return null;

    const matrix = (latestReport.matrix as Array<Record<string, unknown>> | undefined) ?? [];
    const ownMatrixEntry = matrix.find(
      (entry) => String(entry.document_id ?? "") === String(mySubmission.documentId)
    );
    return (ownMatrixEntry?.student_report_id as string | undefined) ?? null;
  }, [latestReport, mySubmission]);

  const {
    data: studentReport,
    isLoading: loadingStudentReport,
    isError: isStudentReportError,
    error: studentReportError,
  } = useStudentReport(studentReportId);

  const ownershipMismatch =
    Boolean(studentReport?.document_id) &&
    Boolean(mySubmission?.documentId) &&
    studentReport?.document_id !== mySubmission?.documentId;

  const isLoading =
    !hydrated ||
    loadingReports ||
    loadingSubmissions ||
    (Boolean(studentReportId) && loadingStudentReport);

  const docIdToName = useMemo(() => {
    const map = new Map<string, string>();
    (submissions ?? []).forEach((s) => {
      if (s.documentId) {
        map.set(s.documentId, s.studentName || "Unknown student");
      }
    });
    return map;
  }, [submissions]);

  const comparisons = useMemo<ComparisonRow[]>(() => {
    if (!studentReport?.comparisons || !Array.isArray(studentReport.comparisons)) return [];

    return studentReport.comparisons
      .map((item) => {
        if (typeof item !== "object" || item === null) return null;
        const row = item as Record<string, unknown>;

        const documentId = String(row.document_id ?? "").trim();
        const similarity = Number(row.similarity ?? 0);
        const matchedPassages = Number(row.matched_passages ?? row.passages ?? 0);

        if (!documentId) return null;
        return {
          documentId,
          similarity: Number.isFinite(similarity) ? similarity : 0,
          matchedPassages: Number.isFinite(matchedPassages) ? matchedPassages : 0,
        };
      })
      .filter((item): item is ComparisonRow => item !== null);
  }, [studentReport]);

  const score = Number(studentReport?.plagiarism_score ?? 0);
  const tone = scoreTone(score);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800 dark:hover:text-white"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Plagiarism Report</h1>
        </div>
        <LoadingState />
      </div>
    );
  }

  const has404 = studentReportError?.message?.includes("404");
  const hasReport = Boolean(studentReportId && studentReport && !ownershipMismatch);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800 dark:hover:text-white"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">My Plagiarism Report</h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {assignment?.title ?? "Assignment"}
            </p>
          </div>
        </div>

        <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          <ShieldCheck className="h-3.5 w-3.5" />
          Student-only view
        </span>
      </div>

      {!hasReport && (
        <div className="rounded-2xl border border-slate-200 bg-white p-8 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 text-slate-500" />
            <div>
              <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                Your report is not available yet
              </h2>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                {ownershipMismatch
                  ? "We could not verify report ownership for your submission."
                  : has404
                    ? "Your instructor has not published your report yet."
                    : isStudentReportError
                      ? "We could not load your report right now. Please try again shortly."
                      : "Your instructor may still be processing or publishing reports."}
              </p>
            </div>
          </div>
        </div>
      )}

      {hasReport && (
        <>
          <section className={`rounded-2xl border p-6 ${tone.bg} border-slate-200 dark:border-slate-800`}>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">
              Your Plagiarism Score
            </p>
            <div className="mt-3 flex items-end justify-between gap-3">
              <p className={`text-5xl font-black leading-none ${tone.text}`}>
                {(score).toFixed(1)}%
              </p>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${tone.chip}`}>
                {tone.label}
              </span>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Comparison Details</h2>

            {comparisons.length === 0 ? (
              <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
                No comparison entries were found for this report.
              </p>
            ) : (
              <div className="mt-4 space-y-3">
                {comparisons.map((row, index) => {
                  const rowTone = scoreTone(row.similarity);
                  const matchedName = docIdToName.get(row.documentId) || "Unknown student";

                  return (
                    <div
                      key={`${row.documentId}-${index}`}
                      className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-800/40"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                            Matched student
                          </p>
                          <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">
                            {matchedName}
                          </p>
                        </div>
                        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${rowTone.chip}`}>
                          {(row.similarity * 100).toFixed(1)}%
                        </span>
                      </div>
                      <p className="mt-3 text-xs text-slate-600 dark:text-slate-400">
                        Matched passages: <span className="font-semibold">{row.matchedPassages}</span>
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}