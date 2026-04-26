import { Submission } from "@/features/teacher/api";
import { CheckCircle2, Clock, XCircle } from "lucide-react";
import clsx from "clsx";

interface SubmissionRowProps {
  submission: Submission;
}

export function SubmissionRow({ submission }: SubmissionRowProps) {
  const isSubmitted = submission.status === "submitted";
  const isProcessing = submission.status === "processing";
  const isFailed = submission.status === "failed";
  const isMissing = submission.status === "not_submitted";

  return (
    <div className="flex items-center justify-between border-b border-slate-200 py-4 last:border-0 dark:border-slate-800">
      <div className="flex items-center gap-4">
        <div className="flex flex-col">
          <span className="font-medium text-slate-800 dark:text-slate-200">
            {submission.studentName || "Unknown Student"}
          </span>
          {isSubmitted && submission.submittedAt ? (
            <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-1 dark:text-slate-400">
              <Clock className="h-3.5 w-3.5" />
              <span>{new Date(submission.submittedAt).toLocaleString()}</span>
            </div>
          ) : isMissing ? (
             <div className="text-xs text-slate-400 mt-1 italic dark:text-slate-500">
              No submission yet
            </div>
          ) : isProcessing ? (
            <div className="text-xs text-blue-500 mt-1 animate-pulse dark:text-blue-400">
              System is processing...
            </div>
          ) : (
            <div className="text-xs text-red-500 mt-1 dark:text-red-400">
              Submission failed
            </div>
          )}
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        {submission.documentId && (
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api/v1"}/documents/${submission.documentId}/download`}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => console.log('View PDF button clicked - Document ID:', submission.documentId)}
            className="text-xs font-bold text-blue-600 hover:text-blue-700 bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-100 transition-colors dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800"
          >
            View PDF
          </a>
        )}
        <span
          className={clsx(
            "inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full border",
            isSubmitted
              ? "bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800"
              : isProcessing
                ? "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800"
                : isFailed
                  ? "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-800"
                  : "bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800"
          )}
        >
          {isSubmitted ? (
            <>
              <CheckCircle2 className="h-3.5 w-3.5" />
              Submitted
            </>
          ) : isProcessing ? (
            <>
              <Clock className="h-3.5 w-3.5 animate-spin" />
              Processing
            </>
          ) : isFailed ? (
            <>
              <XCircle className="h-3.5 w-3.5" />
              Failed
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
