"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import {
  fetchAssignmentById,
  fetchAssignmentReports,
  fetchSubmissions,
  useCourseStudents,
  getLatestReport,
  usePublishReports,
} from "@/features/teacher/api";
import { PlagiarismReport } from "@/components/plagiarism/PlagiarismReport";
import { useAuthStore } from "@/store/authStore";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

type ReportLike = {
  documents?: unknown;
  matrix?: unknown;
  [key: string]: unknown;
};

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === "object" && value !== null;
};

const getDocLabel = (documentId: unknown, labels: Map<string, string>): string => {
  const id = String(documentId ?? "");
  return labels.get(id) ?? id;
};

const withStudentNames = (rawReport: unknown, labels: Map<string, string>): unknown => {
  if (!isRecord(rawReport)) return rawReport;

  const report = rawReport as ReportLike;

  const documents = Array.isArray(report.documents)
    ? (report.documents as unknown[]).map((docId) => getDocLabel(docId, labels))
    : report.documents;

  const matrix = Array.isArray(report.matrix)
    ? (report.matrix as Array<Record<string, unknown>>).map((row) => {
        const comparisons = Array.isArray(row.comparisons)
          ? (row.comparisons as Array<Record<string, unknown>>).map((cmp) => ({
              ...cmp,
              document_id: getDocLabel(cmp.document_id, labels),
            }))
          : row.comparisons;

        return {
          ...row,
          document_id: getDocLabel(row.document_id, labels),
          comparisons,
        };
      })
    : report.matrix;

  return {
    ...report,
    documents,
    matrix,
  };
};

export default function TeacherAssignmentReportPage() {
  const { courseId, assignmentId } = useParams() as { courseId: string; assignmentId: string };
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const hydrated = useAuthStore((s) => s.hydrated);
  const isTeacher = user?.role === "teacher";
  const [published, setPublished] = useState(false);
  const publishReportsMutation = usePublishReports();

  useEffect(() => {
    if (!hydrated) {
      return;
    }

    if (!user) {
      router.replace("/login");
      return;
    }

    if (user.role !== "teacher") {
      router.replace("/dashboard/student");
    }
  }, [hydrated, user, router]);

  const {
    data: reports,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["assignmentReports", assignmentId],
    queryFn: () => fetchAssignmentReports(assignmentId),
    enabled: Boolean(assignmentId) && isTeacher,
    staleTime: 5000,
    gcTime: 10 * 60 * 1000,
  });

  const { data: assignment, isLoading: loadingAssignment } = useQuery({
    queryKey: ["assignment", assignmentId],
    queryFn: () => fetchAssignmentById(assignmentId),
    enabled: Boolean(assignmentId) && isTeacher,
    staleTime: 30 * 1000,
    gcTime: 10 * 60 * 1000,
  });

  const { data: submissions, isLoading: loadingSubmissions } = useQuery({
    queryKey: ["submissions", assignmentId],
    queryFn: () => fetchSubmissions(assignmentId),
    enabled: Boolean(assignmentId) && isTeacher,
    staleTime: 30 * 1000,
    gcTime: 10 * 60 * 1000,
  });

  const { data: students } = useCourseStudents(courseId);

  const latestReport = useMemo(() => {
    return getLatestReport(reports ?? []);
  }, [reports]);

  const documentLabels = useMemo(() => {
    const map = new Map<string, string>();
    (submissions ?? []).forEach((s) => {
      if (s.documentId) {
        map.set(s.documentId, s.studentName);
      }
    });
    return map;
  }, [submissions]);

  const displayReport = useMemo(() => {
    return withStudentNames(latestReport ?? null, documentLabels);
  }, [latestReport, documentLabels]);

  if (!hydrated) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!user || !isTeacher) return null;

  if (isLoading || loadingAssignment || loadingSubmissions) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-5xl space-y-4">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Plagiarism Report</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">Failed to load reports.</p>
      </div>
    );
  }

  const handlePublishReports = async () => {
    try {
      await publishReportsMutation.mutateAsync(assignmentId);
      setPublished(true);
      toast.success("Reports are now visible to students");
    } catch (error) {
      console.error("Failed to publish reports:", error);
      toast.error(error instanceof Error ? error.message : "Failed to publish reports");
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          Plagiarism Report{assignment?.title ? ` — ${assignment.title}` : ""}
        </h1>

        <button
          type="button"
          onClick={handlePublishReports}
          disabled={published || publishReportsMutation.isPending}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {publishReportsMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Publishing...
            </>
          ) : published ? (
            "Published"
          ) : (
            "Publish Reports to Students"
          )}
        </button>
      </div>
      <PlagiarismReport
        report={displayReport ?? null}
        submissions={submissions}
        students={students}
      />
    </div>
  );
}
