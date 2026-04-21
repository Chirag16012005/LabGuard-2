"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { Loader2, ArrowLeft, Upload, FileCheck, Calendar, Info, Clock, CheckCircle2, AlertCircle, Eye } from "lucide-react";
import { useStudentCourse } from "@/features/student/api";
import { useAssignment } from "@/features/teacher/api"; // Reuse teacher query to avoid duplication
import { useSubmitAssignment, useStudentSubmission } from "@/features/student/api";
import { useAuthStore } from "@/store/authStore";
import { toast } from "sonner";

export default function StudentAssignmentPage() {
  const { courseId, assignmentId } = useParams() as { courseId: string; assignmentId: string };
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const { data: course, isLoading: loadingCourse } = useStudentCourse(courseId);
  const { data: assignment, isLoading: loadingAssignment } = useAssignment(assignmentId);
  const { data: submission, isLoading: loadingSubmission } = useStudentSubmission(assignmentId, user?.id ?? null);

  const { mutate: submit, isPending: submitting } = useSubmitAssignment();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type !== "application/pdf") {
        toast.error("Only PDF files are allowed");
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleSubmit = () => {
    if (!selectedFile) return;

    submit({assignmentId, file: selectedFile },
      {
        onSuccess: () => {
          toast.success("Assignment submitted successfully!");
          setSelectedFile(null);
        },
        onError: (error) => {
          toast.error(error instanceof Error ? error.message : "Failed to submit assignment");
        },
      }
    );
  };

  if (
    loadingCourse ||
    loadingAssignment ||
    loadingSubmission
  ) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!assignment || !course) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <p className="text-slate-500 font-medium">Assignment or course not found.</p>
        <button
          onClick={() => router.push(`/dashboard/student/courses/${courseId}`)}
          className="text-blue-500 hover:text-blue-600 font-medium"
        >
          Back to Course
        </button>
      </div>
    );
  }

  const isOverdue = assignment.dueDate && new Date() > new Date(assignment.dueDate);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push(`/dashboard/student/courses/${courseId}`)}
          className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <nav className="flex items-center gap-2 text-sm text-slate-500 mb-1">
            <span className="hover:text-slate-900 cursor-pointer" onClick={() => router.push("/dashboard/student")}>Dashboard</span>
            <span>/</span>
            <span className="hover:text-slate-900 cursor-pointer" onClick={() => router.push(`/dashboard/student/courses/${courseId}`)}>{course.title}</span>
          </nav>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            {assignment.title}
          </h1>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content: Info & Description */}
        <div className="lg:col-span-2 space-y-6">
          <section className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <Info className="h-5 w-5 text-blue-500" />
              Description
            </h3>
            <div className="prose prose-slate dark:prose-invert max-w-none">
              {assignment.description || (
                <p className="text-slate-500 italic">No description provided for this assignment.</p>
              )}
            </div>
          </section>

          {/* Submission Status for Student */}
          <section className={`rounded-2xl p-6 border ${
            submission 
              ? "bg-green-50 border-green-200 dark:bg-green-900/10 dark:border-green-800/40" 
              : isOverdue
                ? "bg-red-50 border-red-200 dark:bg-red-900/10 dark:border-red-800/40"
                : "bg-blue-50 border-blue-200 dark:bg-blue-900/10 dark:border-blue-800/40"
          }`}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                {submission ? (
                  <>
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                    Assignment Submitted
                  </>
                ) : isOverdue ? (
                  <>
                    <AlertCircle className="h-5 w-5 text-red-500" />
                    Overdue
                  </>
                ) : (
                  <>
                    <Clock className="h-5 w-5 text-blue-500" />
                    Pending Submission
                  </>
                )}
              </h3>
              {submission && (
                <span className="text-sm font-medium text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-950 px-3 py-1 rounded-full">
                  Status: {submission.status}
                </span>
              )}
            </div>

            {submission ? (
              <div className="space-y-6">
                <div className="flex items-center gap-4 bg-white/50 dark:bg-slate-800/20 p-4 rounded-xl border border-green-100 dark:border-green-900/30">
                  <div className="p-3 bg-green-100 dark:bg-green-900/40 rounded-lg">
                    <FileCheck className="h-6 w-6 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-slate-900 dark:text-white">Submission Received</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      Logged on {new Date(submission.submittedAt!).toLocaleString()}
                    </p>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-3">
                  <button
                    disabled
                    className="flex-1 py-3 px-4 bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 rounded-xl font-bold cursor-not-allowed opacity-60"
                  >
                    Submission Locked
                  </button>
                </div>

                <p className="text-[10px] text-center text-slate-400 dark:text-slate-500 italic">
                  Only one submission is permitted per student. To correct an error, please contact your instructor.
                </p>
              </div>
            ) : isOverdue ? (
              <p className="text-sm text-red-600 dark:text-red-400">
                The deadline for this assignment has passed. You can no longer submit your work.
              </p>
            ) : (
              <div className="space-y-6">
                <p className="text-sm text-blue-700 dark:text-blue-400">
                  Please upload your work in PDF format. Make sure your file is final before submitting.
                </p>

                <div className="space-y-4">
                  <label className="block">
                    <div className={`mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-xl transition-colors cursor-pointer ${
                      selectedFile ? "border-blue-400 bg-blue-50/50 dark:border-blue-500/40 dark:bg-blue-900/5" : "border-slate-300 hover:border-blue-400 dark:border-slate-700"
                    }`}>
                      <div className="space-y-1 text-center">
                        <Upload className={`mx-auto h-12 w-12 ${selectedFile ? "text-blue-500" : "text-slate-400"}`} />
                        <div className="flex text-sm text-slate-600 dark:text-slate-400">
                          <label className="relative cursor-pointer rounded-md font-semibold text-blue-600 hover:text-blue-500">
                            <span>{selectedFile ? "Change file" : "Upload a file"}</span>
                            <input type="file" className="sr-only" onChange={handleFileChange} accept=".pdf" />
                          </label>
                          {!selectedFile && <p className="pl-1">or drag and drop</p>}
                        </div>
                        <p className="text-xs text-slate-500">
                          {selectedFile ? selectedFile.name : "PDF up to 10MB"}
                        </p>
                      </div>
                    </div>
                  </label>

                  <button
                    onClick={handleSubmit}
                    disabled={!selectedFile || submitting}
                    className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white rounded-xl font-bold transition-all shadow-lg shadow-blue-200 dark:shadow-none flex items-center justify-center gap-2"
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="h-5 w-5 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      "Submit Assignment"
                    )}
                  </button>
                </div>
              </div>
            )}
          </section>

          {/* Plagiarism Report Section */}
          {submission && (
            <section className="space-y-4">
              <button
                onClick={() => router.push(`/dashboard/student/assignment/${assignmentId}/report`)}
                className="w-full py-4 px-6 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white rounded-xl font-bold transition-all shadow-lg shadow-purple-200 dark:shadow-none flex items-center justify-center gap-2"
              >
                <Eye className="h-5 w-5" />
                View My Plagiarism Report
              </button>
            </section>
          )}
        </div>

        {/* Sidebar: Meta info */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
            <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400">Details</h4>
            
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <Calendar className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <p className="text-xs text-slate-500 uppercase font-bold tracking-tight">Due Date</p>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">
                    {assignment.dueDate ? new Date(assignment.dueDate).toLocaleString() : "No deadline"}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Clock className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <p className="text-xs text-slate-500 uppercase font-bold tracking-tight">Status</p>
                  <p className={`text-sm font-bold ${submission ? "text-green-600" : "text-blue-600"}`}>
                    {submission ? "Submitted" : "Not Submitted"}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
