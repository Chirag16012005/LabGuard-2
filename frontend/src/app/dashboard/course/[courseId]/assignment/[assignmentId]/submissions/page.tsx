"use client";

import { useParams, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { useAssignment, useSubmissions, useRunPlagiarism } from "@/features/teacher/api";
import { SubmissionRow } from "@/components/ui/submission-row";
import { Loader2, ArrowLeft, Users } from "lucide-react";
import { toast } from "sonner";

export default function AssignmentSubmissionsPage() {
  const { courseId, assignmentId } = useParams() as { courseId: string; assignmentId: string };
  const { data: assignment, isLoading: loadingAssignment } = useAssignment(assignmentId);
  const { data: submissions, isLoading: loadingSubmissions } = useSubmissions(assignmentId);
  const router = useRouter();

  const { user } = useAuthStore();
  const isTeacher = user?.role === "teacher";
  const runPlagiarismMutation = useRunPlagiarism();

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

  const handleRunPlagiarismCheck = async () => {
    try {
      await runPlagiarismMutation.mutateAsync(assignmentId);
      toast.success("Plagiarism report generated");
      router.push(`/dashboard/teacher/courses/${courseId}/assignment/${assignmentId}/report`);
    } catch (error) {
      console.error("Failed to run plagiarism check:", error);
      toast.error(error instanceof Error ? error.message : "Failed to run plagiarism check");
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
          <button
            type="button"
            onClick={handleRunPlagiarismCheck}
            disabled={eligibleForPlagiarismCount < 2 || runPlagiarismMutation.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {runPlagiarismMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Running...
              </>
            ) : (
              "Run Plagiarism Check"
            )}
          </button>
        )}
      </div>

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
