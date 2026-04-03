import { Submission } from "@/features/teacher/api";
import { CheckCircle2, Clock, XCircle } from "lucide-react";
import clsx from "clsx";

interface SubmissionRowProps {
  submission: Submission;
}

export function SubmissionRow({ submission }: SubmissionRowProps) {
  const isSubmitted = submission.status === "submitted";

  return (
    <div className="flex items-center justify-between border-b border-slate-200 py-4 last:border-0 dark:border-slate-800">
      <div className="flex items-center gap-4">
        <div className="flex flex-col">
          <span className="font-medium text-slate-800 dark:text-slate-200">
            {submission.studentName}
          </span>
          {isSubmitted && submission.submittedAt ? (
            <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-1 dark:text-slate-400">
              <Clock className="h-3.5 w-3.5" />
              <span>{new Date(submission.submittedAt).toLocaleString()}</span>
            </div>
          ) : (
             <div className="text-xs text-slate-500 mt-1 dark:text-slate-400">
              No submission early
            </div>
          )}
        </div>
      </div>
      
      <div>
        <span
          className={clsx(
            "inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full border",
            isSubmitted
              ? "bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800"
              : "bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800"
          )}
        >
          {isSubmitted ? (
            <>
              <CheckCircle2 className="h-3.5 w-3.5" />
              Submitted
            </>
          ) : (
            <>
              <XCircle className="h-3.5 w-3.5" />
              Missing
            </>
          )}
        </span>
      </div>
    </div>
  );
}
