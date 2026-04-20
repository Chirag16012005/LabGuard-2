"use client";

import { useParams, useRouter } from "next/navigation";
import { Loader2, ArrowLeft, FileText } from "lucide-react";
import { useStudentCourse, useStudentAssignments } from "@/features/student/api";
import { AssignmentCard } from "@/components/ui/assignment-card";

export default function StudentCourseDetailPage() {
  const { courseId } = useParams() as { courseId: string };
  const router = useRouter();

  const { data: course, isLoading: loadingCourse } = useStudentCourse(courseId);
  const {
    data: assignments,
    isLoading: loadingAssignments,
    isError,
    error,
  } = useStudentAssignments(courseId);

  if (loadingCourse || loadingAssignments) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!course) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <p className="text-slate-500 font-medium">Course not found.</p>
        <button
          onClick={() => router.push("/dashboard/student")}
          className="text-blue-500 hover:text-blue-600 font-medium"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => router.push("/dashboard/student")}
          className="p-2 -ml-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-colors dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            {course.title}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {course.subtitle}
          </p>
        </div>
      </div>

      {/* Section title */}
      <div className="border-b border-slate-200 pb-4 dark:border-slate-800">
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">
          Assignments
        </h2>
      </div>

      {/* Error state */}
      {isError && (
        <div className="flex flex-col items-center justify-center h-48 border-2 border-dashed border-red-200 rounded-xl p-6 dark:border-red-800/40">
          <p className="text-red-500 font-medium">
            Failed to load assignments
          </p>
          <p className="text-sm text-slate-500 mt-1">
            {error instanceof Error ? error.message : "Please try again later."}
          </p>
        </div>
      )}

      {/* Empty state */}
      {!isError && assignments?.length === 0 && (
        <div className="flex flex-col items-center justify-center h-48 border-2 border-dashed border-slate-200 rounded-xl p-6 dark:border-slate-800">
          <FileText className="h-10 w-10 text-slate-300 dark:text-slate-600 mb-3" />
          <p className="text-slate-500 font-medium dark:text-slate-400">
            No assignments yet
          </p>
          <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">
            Your teacher hasn&apos;t added any assignments to this course.
          </p>
        </div>
      )}

      {/* Assignment list */}
      {!isError && assignments && assignments.length > 0 && (
        <div className="space-y-3">
          {assignments.map((assignment) => (
            <AssignmentCard 
              key={assignment.id} 
              assignment={assignment} 
              href={`/dashboard/student/courses/${courseId}/assignment/${assignment.id}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
