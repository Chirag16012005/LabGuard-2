"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useAuthStore } from "@/store/authStore";
import {
  fetchAssignmentReports,
  pollDetectionJob,
  useAssignment,
  useAssignmentClusters,
  useCourseStudents,
  useSubmissions,
  useRunPlagiarism,
} from "@/features/teacher/api";
import { SubmissionRow } from "@/components/ui/submission-row";
import ClusterCard from "@/components/ClusterCard";
import { Loader2, ArrowLeft, Users } from "lucide-react";
import { toast } from "sonner";

export default function AssignmentSubmissionsPage() {
  const { courseId, assignmentId } = useParams() as { courseId: string; assignmentId: string };
  const { data: assignment, isLoading: loadingAssignment } = useAssignment(assignmentId);
  const { data: submissions, isLoading: loadingSubmissions } = useSubmissions(assignmentId);
  const { data: students } = useCourseStudents(courseId);
  const router = useRouter();

  const { user } = useAuthStore();
  const isTeacher = user?.role === "teacher";
  const runPlagiarismMutation = useRunPlagiarism();
  const {
    data: clusterData,
    isFetching: isLoadingClusters,
    isError: isClusterError,
    error: clusterError,
    isFetched: hasFetchedClusters,
    refetch: refetchClusters,
  } = useAssignmentClusters(assignmentId);
  const [isPollingDetection, setIsPollingDetection] = useState(false);

  if (loadingAssignment || loadingSubmissions) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!assignment) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4 text-slate-500">
        Assignment not found.
      </div>
    );
  }

  const totalSubmissions = submissions?.filter((s) => s.status === "submitted").length || 0;
  const totalStudents = submissions?.length || 0;

  const eligibleForPlagiarismCount =
    submissions?.filter((s) => s.status === "submitted" || s.status === "processing").length || 0;

  const studentIdToName = new Map((students ?? []).map((student) => [student.id, student.fullName]));
  const documentIdToStudentName = new Map(
    (submissions ?? [])
      .filter((submission) => Boolean(submission.documentId))
      .map((submission) => {
        const resolvedName =
          studentIdToName.get(submission.studentId) ||
          submission.studentName ||
          "Unknown student";
        return [submission.documentId as string, resolvedName] as const;
      })
  );

  const handleRunPlagiarismCheck = async () => {
    if (isPollingDetection || runPlagiarismMutation.isPending) {
      return;
    }

    if (!assignmentId) {
      toast.error("Missing assignment ID");
      return;
    }

    const loadingToastId = toast.loading("Processing...");

    try {
      setIsPollingDetection(true);
      const result = await runPlagiarismMutation.mutateAsync(assignmentId);
      const jobId = result?.job_id;

      if (!jobId) {
        throw new Error("Detection did not return a valid job_id");
      }

      console.log("Job ID:", jobId);

      const job = await pollDetectionJob(jobId, {
        onUpdate: (status) => {
          console.log("Job status update:", status);
        },
      });

      console.log("FINAL JOB:", job);

      const finalStatus = String(job.status ?? "").toLowerCase();
      if (finalStatus !== "completed") {
        throw new Error(`Detection job did not complete successfully. Current status: ${job.status}`);
      }

      const reports = await fetchAssignmentReports(assignmentId);
      console.log("[plagiarism] Reports fetched after completion", {
        assignmentId,
        reportCount: reports.length,
        reportId: reports[0]?.report_id,
      });

      toast.success("Report ready", { id: loadingToastId });

      // console.log("[plagiarism] Navigating to report page", { courseId, assignmentId, jobId: job.job_id });

      router.push(`/dashboard/teacher/courses/${courseId}/assignment/${assignmentId}/report`);
    } catch (error) {
      console.error("Failed to run plagiarism check:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to run plagiarism check";
      toast.error(errorMessage, { id: loadingToastId });
    } finally {
      setIsPollingDetection(false);
    }
  };

  const handleViewClusters = async () => {
    if (!assignmentId || isLoadingClusters) {
      return;
    }

    const result = await refetchClusters();
    if (result.error) {
      const errorMessage = result.error instanceof Error
        ? result.error.message
        : "Failed to fetch clusters";
      toast.error(errorMessage);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3 mb-6">
         <button 
           onClick={() => router.push(`/dashboard/course/${courseId}`)}
           className="p-2 -ml-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-colors dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
         >
           <ArrowLeft className="h-5 w-5" />
         </button>
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white truncate">
            {assignment.title}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-2">
            <Users className="h-4 w-4" />
            {totalSubmissions} / {totalStudents} Submitted
          </p>
        </div>

        {isTeacher && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleViewClusters}
              disabled={isLoadingClusters}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              {isLoadingClusters ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading clusters...
                </>
              ) : (
                "View Clusters"
              )}
            </button>

            <button
              type="button"
              onClick={handleRunPlagiarismCheck}
              disabled={eligibleForPlagiarismCount < 2 || runPlagiarismMutation.isPending || isPollingDetection}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {runPlagiarismMutation.isPending || isPollingDetection ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                "Run Plagiarism Check"
              )}
            </button>
          </div>
        )}
      </div>

      {isClusterError && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/30 dark:text-red-300">
          {(clusterError as Error)?.message || "Failed to fetch clusters."}
        </div>
      )}

      {isLoadingClusters && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-900/50 dark:text-slate-300">
          Loading clusters...
        </div>
      )}

      {hasFetchedClusters && !isLoadingClusters && !isClusterError && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-base font-semibold text-slate-800 dark:text-slate-200">Clusters</h2>
          {clusterData?.clusters?.length ? (
            <div className="mt-3 space-y-3">
              {clusterData.clusters.map((cluster, index) => (
                <ClusterCard
                  key={cluster.cluster_id}
                  cluster={cluster}
                  clusterLabel={`Cluster #${index + 1}`}
                  memberNames={cluster.members.map(
                    (documentId) => documentIdToStudentName.get(documentId) || "Unknown student"
                  )}
                />
              ))}
            </div>
          ) : (
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">🎉 No suspicious similarity clusters found</p>
          )}
        </div>
      )}

      <div className="border-b border-slate-200 pb-4 dark:border-slate-800">
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">
          Student Submissions
        </h2>
      </div>

      {(!submissions || submissions.length === 0) ? (
        <div className="flex h-32 items-center justify-center border-2 border-dashed border-slate-200 rounded-xl bg-slate-50 dark:border-slate-800 dark:bg-slate-900/50">
          <p className="text-slate-500 font-medium dark:text-slate-400">
            No submissions yet
          </p>
        </div>
      ) : (
        <div className="border-t border-slate-200 bg-white dark:bg-slate-900 dark:border-slate-800 rounded-xl px-5 py-2">
          {submissions.map((submission) => (
            <SubmissionRow key={submission.id} submission={submission} />
          ))}
        </div>
      )}
    </div>
  );
}
