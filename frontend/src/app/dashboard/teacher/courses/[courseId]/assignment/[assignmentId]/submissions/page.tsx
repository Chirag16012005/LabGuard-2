  "use client";

  import { useParams, useRouter } from "next/navigation";
  import { useState, useMemo, useEffect } from "react";
  import {
    useAssignment,
    useSubmissions,
    useCourseStudents,
    pollDetectionJob,
    useRunPlagiarism,
    Submission,
  } from "@/features/teacher/api";
  import { SubmissionRow } from "@/components/ui/submission-row";
  import { Loader2, ArrowLeft, FileStack, Search, CheckCircle2, Clock, AlertCircle } from "lucide-react";
  import { toast } from "sonner";

  type DetectionUiStatus = "idle" | "running" | "completed" | "error";

  export default function TeacherAssignmentSubmissionsPage() {
    const { courseId, assignmentId } = useParams() as { courseId: string; assignmentId: string };
    const { data: assignment, isLoading: loadingAssignment } = useAssignment(assignmentId);
    const { data: submissions, isLoading: loadingSubmissions } = useSubmissions(assignmentId);
    const { data: students, isLoading: loadingStudents } = useCourseStudents(courseId);
    const router = useRouter();

    const [searchTerm, setSearchTerm] = useState("");
    const [statusFilter, setStatusFilter] = useState<string>("all");
    const [isPreparingReport, setIsPreparingReport] = useState(false);
    const [detectionStatus, setDetectionStatus] = useState<DetectionUiStatus>("idle");
    const [latestJobStatus, setLatestJobStatus] = useState<string | null>(null);
    const runPlagiarismMutation = useRunPlagiarism();
    const submissionCount = submissions?.length ?? 0;
    const canRunPlagiarism = submissionCount >= 2;
    const isRunningDetection = runPlagiarismMutation.isPending || isPreparingReport;

    // Debug: Log when students data arrives
    useEffect(() => {
      console.log("📊 Students data received:", {
        count: students?.length,
        firstStudent: students?.[0],
        loading: loadingStudents,
      });
    }, [students, loadingStudents]);

    // Debug: Log submissions data
    useEffect(() => {
      console.log("📋 Submissions data received:", {
        count: submissions?.length,
        firstSubmission: submissions?.[0],
        loading: loadingSubmissions,
      });
    }, [submissions, loadingSubmissions]);

    const mergedSubmissions = useMemo(() => {
      if (!students || !submissions) {
        console.warn("⚠️ Missing data for merge:", { studentsLoaded: !!students, submissionsLoaded: !!submissions });
        return [];
      }

      if (students.length === 0) {
        console.warn("⚠️ No students found for course:", courseId);
      }

      if (students.length > 0 && !students[0].fullName) 
      {
        console.warn("Student name missing from API response:", {
          student: students[0],
          fields: Object.keys(students[0]),
        });
      }

      const statusWeight: Record<string, number> = {
        submitted: 1,
        processing: 4,
        failed: 3,
        not_submitted: 4
      };

      const all = students.map(student => {
        const submission = submissions.find(s => s.studentId === student.id);
        // Use fallbacks to ensure we always have a name
        const studentName = student.fullName || student.email || "Unknown Student";
        
        if (submission) {
          // Ensure studentName is populated from students lookup
          // (backend may return student_id only, not student_name)
          return {
            ...submission,
            studentName,
          };
        }
        
        return {
          assignmentId,
          studentId: student.id,
          studentName,
          status: "not_submitted" as const,
        } as Submission;
      });

      return all
        .filter(s => {
          const matchesSearch = (s.studentName || "").toLowerCase().includes(searchTerm.toLowerCase());
          const matchesFilter = statusFilter === "all" 
            ? true 
            : statusFilter === "missing" 
              ? s.status === "not_submitted" 
              : s.status === "submitted" || s.status === "processing";
          return matchesSearch && matchesFilter;
        })
        .sort((a, b) => {
          const weightA = statusWeight[a.status] || 99;
          const weightB = statusWeight[b.status] || 99;
          if (weightA !== weightB) return weightA - weightB;
          const nameA = (a.studentName || "").toLowerCase();
          const nameB = (b.studentName || "").toLowerCase();
          return nameA.localeCompare(nameB);
        });
    }, [students, submissions, searchTerm, statusFilter, assignmentId, courseId]);

    // Count valid submissions for plagiarism check
    const validSubmissions = mergedSubmissions.filter(
      s => s.status === "submitted" || s.status === "processing"
    );

    const submittedCount = validSubmissions.length;
    const totalCount = students?.length || 0;

    if (loadingAssignment || loadingSubmissions || loadingStudents) {
      return (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
        </div>
      );
    }

    if (!assignment) {
      return (
        <div className="flex flex-col items-center justify-center h-64 space-y-4">
          <p className="text-slate-500 font-medium">Assignment not found.</p>
          <button
            onClick={() => router.push(`/dashboard/course/${courseId}`)}
            className="text-blue-500 hover:text-blue-600 font-medium"
          >
            Back to Course Detail
          </button>
        </div>
      );
    }

    const handleRunPlagiarismCheck = async () => {
      if (isRunningDetection) {
        return;
      }

      if (!assignmentId || !courseId) {
        toast.error("Missing assignment or course ID");
        return;
      }

      if (!canRunPlagiarism) {
        toast.error("At least 2 submissions required for plagiarism detection");
        return;
      }

      const loadingToastId = toast.loading("Starting plagiarism check...");

      try {
        console.log("[plagiarism] Starting detection run", { assignmentId, courseId });
        setIsPreparingReport(true);
        setDetectionStatus("running");
        setLatestJobStatus("starting");
        toast.loading("Submitting plagiarism job...", { id: loadingToastId });

        const job = await runPlagiarismMutation.mutateAsync(assignmentId);

        if (!job?.job_id) {
          throw new Error("Detection job did not return a valid job id");
        }

        console.log("[plagiarism] Detection job created", {
          assignmentId,
          courseId,
          jobId: job.job_id,
          status: job.status,
        });
        toast.loading("Running plagiarism detection...", { id: loadingToastId });

        const finalJob = await pollDetectionJob(job.job_id, {
          onUpdate: (status) => {
            setLatestJobStatus(status);
            console.log("[plagiarism] Poll update", {
              assignmentId,
              courseId,
              jobId: job.job_id,
              status,
            });
          },
        });

        console.log("FINAL JOB:", finalJob);

        setDetectionStatus("completed");
        console.log("[plagiarism] Detection job completed, navigating to report", {
          assignmentId,
          courseId,
          jobId: finalJob.job_id,
          status: finalJob.status,
          reportId: finalJob.report_id,
        });

        toast.success("Report ready! Redirecting...", { id: loadingToastId });

        console.log("[plagiarism] Redirecting to report page", { assignmentId, courseId });
        router.push(`/dashboard/teacher/courses/${courseId}/assignment/${assignmentId}/report`);
      } catch (error) {
        setDetectionStatus("error");
        console.error("[plagiarism] Failed to run plagiarism check", {
          assignmentId,
          courseId,
          error,
        });
        const errorMessage = error instanceof Error ? error.message : "Failed to run plagiarism check";
        toast.error(errorMessage, { id: loadingToastId });
      } finally {
        setIsPreparingReport(false);
      }
    };

    return (
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push(`/dashboard/course/${courseId}`)}
              className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                {assignment.title}
                <span className="text-[10px] font-bold uppercase tracking-widest bg-blue-600 text-white px-2 py-0.5 rounded shadow-sm">Submissions</span>
              </h1>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Course: <span className="font-semibold">{courseId}</span> • Class Roster: {totalCount} students
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-6 self-end sm:self-auto">
            <button
              type="button"
              onClick={handleRunPlagiarismCheck}
              disabled={!canRunPlagiarism || isRunningDetection}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:bg-blue-600"
            >
              {isRunningDetection ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Running plagiarism detection...
                </>
              ) : (
                <>
                  Run Plagiarism Check
                </>
              )}
            </button>
            {detectionStatus !== "idle" && (
              <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                {detectionStatus === "running" && "Running plagiarism detection..."}
                {detectionStatus === "completed" && "Report ready! Redirecting..."}
                {detectionStatus === "error" && "Error occurred"}
                {detectionStatus === "running" && latestJobStatus ? ` (${latestJobStatus})` : ""}
              </p>
            )}
            <div className="text-right">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Submission Rate</p>
              <p className="text-2xl font-black text-slate-900 dark:text-white">
                {totalCount > 0 ? Math.round((submittedCount / totalCount) * 100) : 0}<span className="text-slate-400 font-light text-sm">%</span>
              </p>
            </div>
            <div className="h-10 w-[1px] bg-slate-200 dark:bg-slate-800"></div>
            <div className="flex flex-col">
              <p className="text-xs font-bold text-slate-900 dark:text-white">
                {submittedCount} / {totalCount}
              </p>
              <p className="text-[10px] text-slate-400 font-medium lowercase">received</p>
            </div>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input 
              type="text"
              placeholder="Search student name..."
              className="w-full pl-10 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <div className="flex items-center gap-2 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl w-full md:w-auto">
            <button 
              onClick={() => setStatusFilter("all")}
              className={`flex-1 md:flex-none px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${statusFilter === "all" ? "bg-white dark:bg-slate-700 text-blue-600 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
            >
              All
            </button>
            <button 
              onClick={() => setStatusFilter("submitted")}
              className={`flex-1 md:flex-none px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${statusFilter === "submitted" ? "bg-white dark:bg-slate-700 text-blue-600 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
            >
              Submitted
            </button>
            <button 
              onClick={() => setStatusFilter("missing")}
              className={`flex-1 md:flex-none px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${statusFilter === "missing" ? "bg-white dark:bg-slate-700 text-blue-600 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
            >
              Missing
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/20 flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                Student Submissions
              </h2>
              <div className="hidden sm:flex items-center gap-4 text-[10px] font-bold text-slate-400 uppercase">
                <span className="flex items-center gap-1"><CheckCircle2 className="h-3 w-3 text-green-500" /> Submitted</span>
                <span className="flex items-center gap-1"><Clock className="h-3 w-3 text-blue-500" /> Processing</span>
                <span className="flex items-center gap-1"><AlertCircle className="h-3 w-3 text-slate-300" /> Not Submitted</span>
              </div>
            </div>

            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {mergedSubmissions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-center">
                  <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-full mb-4">
                    <FileStack className="h-12 w-12 text-slate-300" />
                  </div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">No results found</h3>
                  <p className="text-sm text-slate-500 mt-1">
                    Try adjusting your search or filter to see more students.
                  </p>
                </div>
              ) : (
                <div className="px-1">
                  {mergedSubmissions.map((submission) => (
                    <div key={submission.studentId} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors px-5">
                      <SubmissionRow submission={submission} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }
