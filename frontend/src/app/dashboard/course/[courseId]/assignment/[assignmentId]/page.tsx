"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useAuthStore } from "@/store/authStore";
import { ArrowLeft, Upload, CheckCircle, FileText, Loader2 } from "lucide-react";

// --- Types reflecting original Backend schemas ---
interface AssignmentDetails {
  id: string;
  class_id: string;
  filename: string;
  content_type: string;
  file_type: string;
  size_bytes: number;
  status: string;
  submission_count: number;
  created_at: string;
  description: string | null;
  storage_path: string | null;
}

interface SubmissionSummary {
  id: string;
  assignment_id: string;
  student_id: string;
  document_id: string;
  status: "submitted" | "processing" | "failed";
  submitted_at: string;
}

interface LabData {
  assignment: AssignmentDetails;
  submission: SubmissionSummary | null;
}

// --- Mock API Functions ---
const fetchLabData = async (courseId: string, assignmentId: string): Promise<LabData> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        assignment: {
          id: assignmentId,
          class_id: courseId,
          filename: "Lab 3 - Multithreading and Concurrency",
          content_type: "application/pdf",
          file_type: "pdf",
          size_bytes: 204800,
          status: "published",
          submission_count: 14,
          created_at: "2026-10-01T09:00:00Z",
          description: "In this lab, you will implement a multi-threaded web server that handles concurrent client requests. Ensure you use appropriate synchronization mechanisms like mutexes and semaphores to prevent race conditions. Your submission must include a comprehensive README with instructions to build your code.",
          storage_path: null,
        },
        submission: null, // Initially no submission
      });
    }, 800);
  });
};

const submitLab = async (data: { file: File }): Promise<SubmissionSummary> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        id: "mock_sub_1",
        assignment_id: "mock_assn_1",
        student_id: "mock_student_1",
        document_id: "mock_doc_1",
        status: "submitted",
        submitted_at: new Date().toISOString(),
      });
    }, 1500);
  });
};

// --- Subcomponents ---
function AssignmentHeader({ 
  title, 
  description, 
  createdAt, 
  onBack 
}: { 
  title: string; 
  description: string | null; 
  createdAt: string; 
  onBack: () => void;
}) {
  const formattedDate = new Date(createdAt).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });

  return (
    <div className="flex flex-col gap-4 border-b border-gray-200 pb-6 dark:border-slate-800">
      <button 
        onClick={onBack}
        className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors w-fit dark:hover:text-slate-200"
      >
        <ArrowLeft className="h-4 w-4" strokeWidth={1.5} />
        Back
      </button>
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-800 dark:text-slate-100">{title}</h1>
        <p className="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">Created on {formattedDate}</p>
      </div>
      {description && (
        <p className="text-sm text-slate-600 dark:text-slate-300 max-w-3xl leading-relaxed whitespace-pre-wrap">
          {description}
        </p>
      )}
    </div>
  );
}

function SubmissionCard({ initialSubmission }: { initialSubmission: SubmissionSummary | null }) {
  const [file, setFile] = useState<File | null>(null);
  const [submission, setSubmission] = useState<SubmissionSummary | null>(initialSubmission);
  
  const mutation = useMutation({
    mutationFn: submitLab,
    onSuccess: (data) => {
      setSubmission(data);
      setFile(null); // Clear selected file after successful submission
    }
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = () => {
    if (file) {
      mutation.mutate({ file });
    }
  };

  const isUploading = mutation.isPending;

  return (
    <div className="flex flex-col gap-4 p-5 rounded-xl border border-gray-200 bg-white dark:border-slate-800 dark:bg-slate-900/50">
      <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 tracking-tight">Your Work</h2>
      
      {!submission ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">
          No submission yet
        </p>
      ) : (
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 p-3 rounded-lg dark:bg-emerald-900/20 dark:border-emerald-800/30 dark:text-emerald-400 font-medium">
            <CheckCircle className="h-4 w-4" strokeWidth={1.5} />
            {mutation.isSuccess ? "Last submitted just now" : "Submitted successfully"}
          </div>
          <span className="text-xs text-slate-400 ml-1">Status: {submission.status}</span>
        </div>
      )}
      <div className="flex flex-col gap-2 mt-2">
        <label className="flex flex-col border border-gray-200 rounded-lg p-4 cursor-pointer hover:bg-slate-50 transition-colors dark:border-slate-700 dark:hover:bg-slate-800/80 group">
          <div className="flex items-center gap-3 text-slate-600 dark:text-slate-300">
            <div className="p-2 border border-gray-200 rounded-md bg-white dark:bg-slate-800 dark:border-slate-700">
               <Upload className="h-4 w-4 text-slate-400 group-hover:text-blue-500 transition-colors" strokeWidth={1.5} />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-medium">
                {file ? file.name : "Choose file"}
              </span>
              <span className="text-xs text-slate-400">
                {file ? `${(file.size / 1024).toFixed(1)} KB` : "Browse your device"}
              </span>
            </div>
          </div>
          <input type="file" className="hidden" onChange={handleFileChange} disabled={isUploading} />
        </label>
      </div>

      <button
        onClick={handleSubmit}
        disabled={!file || isUploading}
        className={`mt-2 flex items-center justify-center gap-2 border w-full rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 ${
          !file || isUploading
            ? "border-gray-200 bg-gray-50 text-gray-400 opacity-50 cursor-not-allowed dark:border-slate-800 dark:bg-slate-900 dark:text-slate-500"
            : "border-blue-600 text-blue-600 hover:bg-blue-50 hover:translate-y-[-1px] dark:border-blue-500 dark:text-blue-500 dark:hover:bg-blue-900/20"
        }`}
      >
        {isUploading ? (
          <><Loader2 className="h-4 w-4 animate-spin" /> Uploading...</>
        ) : submission ? (
          "Update Submission"
        ) : (
          "Submit Lab"
        )}
      </button>
    </div>
  );
}

function ReportCard({ 
  hasReport, 
  onReportClick 
}: { 
  hasReport: boolean; 
  onReportClick: () => void;
}) {
  return (
    <div className="flex flex-col gap-4 p-5 rounded-xl border border-gray-200 bg-white dark:border-slate-800 dark:bg-slate-900/50 h-full">
      <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 tracking-tight">Plagiarism Report</h2>
      
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Reports require the backend to process your document. They are tied to a valid submission ID.
      </p>

      <div className="mt-auto pt-4 flex flex-col gap-3">
        {!hasReport && (
          <div className="text-sm text-slate-500 border border-gray-100 bg-gray-50 p-3 rounded-lg dark:bg-slate-800/50 dark:border-slate-700/50 dark:text-slate-400">
            Report not available yet
          </div>
        )}

        <button
          onClick={onReportClick}
          disabled={!hasReport}
          className={`flex items-center justify-center gap-2 border w-full rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 ${
            !hasReport
              ? "border-gray-200 bg-gray-50 text-gray-400 opacity-50 cursor-not-allowed dark:border-slate-800 dark:bg-slate-900 dark:text-slate-500"
              : "border-gray-200 text-slate-700 hover:bg-slate-50 hover:translate-y-[-1px] dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
          }`}
        >
          <FileText className="h-4 w-4" strokeWidth={1.5} />
          View Plagiarism Report
        </button>
      </div>
    </div>
  );
}

// --- Main Page Component ---
export default function AssignmentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const role = useAuthStore((s) => s.user?.role); 
  
  const courseId = params?.courseId as string;
  const assignmentId = params?.assignmentId as string;

  const { data: labData, isLoading } = useQuery({
    queryKey: ['assignmentData', courseId, assignmentId],
    queryFn: () => fetchLabData(courseId, assignmentId),
  });

  const handleBack = () => {
    router.back();
  };

  const handleReportClick = () => {
    router.push("/dashboard/reports/placeholder");
  };

  if (isLoading) {
    return (
      <div className="flex w-full items-center justify-center py-24">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!labData) return null;
  const { assignment, submission } = labData;

  // We consider a report available only if the submission processing implies it's ready.
  // In our mock dataset, the original schema lacked a specific flag, so we'll mock its logic.
  const isReportAvailable = false; 

  return (
    <div className="flex flex-col gap-6 max-w-4xl mx-auto w-full pb-12">
      <AssignmentHeader 
        title={assignment.filename} 
        description={assignment.description} 
        createdAt={assignment.created_at} 
        onBack={handleBack} 
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
        <SubmissionCard initialSubmission={submission} />
        <ReportCard 
          hasReport={isReportAvailable} 
          onReportClick={handleReportClick} 
        />
      </div>
    </div>
  );
}
