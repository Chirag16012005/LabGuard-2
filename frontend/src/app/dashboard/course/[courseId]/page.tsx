"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { useAssignments } from "@/features/courses/api/get-assignments";
import { AssignmentItem } from "@/components/ui/assignment-item";

interface CourseAssignmentsPageProps {
  params: Promise<{ courseId: string }>;
}

export default function CourseAssignmentsPage({ params }: CourseAssignmentsPageProps) {
  const router = useRouter();
  const { courseId } = use(params);

  const courseName = 
    courseId === "course1" ? "Data Structures" : 
    courseId === "course2" ? "Algorithms" : 
    courseId === "course3" ? "Database Systems" : 
    courseId === "course4" ? "Operating Systems" :
    "Course";

  const { data: assignments, isLoading, error } = useAssignments(courseId);

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto min-h-screen">
      <button 
        onClick={() => router.push("/dashboard")}
        className="flex items-center text-sm font-medium text-slate-500 hover:text-sky-600 dark:text-slate-400 dark:hover:text-sky-400 mb-8 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Dashboard
      </button>

      <h1 className="text-2xl font-bold mb-8 text-slate-800 dark:text-slate-100">
        {courseName}
      </h1>

      {isLoading && (
        <div className="flex flex-col gap-4">
          <div className="text-slate-500 dark:text-slate-400 mb-2 font-medium">Loading assignments...</div>
          {[1, 2, 3].map((skeleton) => (
            <div
              key={skeleton}
              className="bg-slate-100 dark:bg-slate-800/80 animate-pulse border border-slate-200 dark:border-slate-800 rounded-lg h-[88px] w-full"
            />
          ))}
        </div>
      )}

      {error && (
        <div className="text-red-500 dark:text-red-400">Failed to load assignments.</div>
      )}

      {!isLoading && !error && assignments?.length === 0 && (
        <div className="flex items-center justify-center p-12 border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-900/50">
          <p className="text-slate-500 dark:text-slate-400">No assignments found</p>
        </div>
      )}

      {!isLoading && !error && assignments && assignments.length > 0 && (
        <div className="flex flex-col gap-4">
          {assignments.map((assignment) => (
            <AssignmentItem key={assignment.id} assignment={assignment} />
          ))}
        </div>
      )}
    </div>
  );
}
