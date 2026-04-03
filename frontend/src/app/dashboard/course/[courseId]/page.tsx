"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useCourse, useAssignments } from "@/features/teacher/api";
import { AssignmentItem } from "@/components/ui/assignment-item";
import { CreateAssignmentForm } from "@/components/ui/create-assignment-form";
import { Loader2, Plus, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function CourseDetailPage() {
  const { courseId } = useParams() as { courseId: string };
  const { data: course, isLoading: loadingCourse } = useCourse(courseId);
  const { data: assignments, isLoading: loadingAssignments } = useAssignments(courseId);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const router = useRouter();

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
        <p className="text-slate-500">Course not found.</p>
        <Link href="/dashboard" className="text-blue-500 hover:text-blue-600 font-medium">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
         <button 
           onClick={() => router.push('/dashboard')}
           className="p-2 -ml-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-colors dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
         >
           <ArrowLeft className="h-5 w-5" />
         </button>
         <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              {course.title}
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              {course.subtitle} &mdash; Manage Assignments
            </p>
         </div>
      </div>

      <div className="flex items-center justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">
          Assignments
        </h2>
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-slate-900 border border-slate-900 rounded-lg hover:translate-y-[-1px] transition-all duration-200 dark:bg-slate-100 dark:text-slate-900 dark:border-slate-100"
        >
          <Plus className="h-4 w-4" />
          Create Assignment
        </button>
      </div>

      {showCreateForm && (
        <div className="mb-8 border border-slate-200 rounded-xl p-5 bg-white dark:bg-slate-900 dark:border-slate-800">
          <h3 className="text-lg font-semibold text-slate-800 mb-4 dark:text-slate-200">
            Create New Assignment
          </h3>
          <CreateAssignmentForm
            courseId={courseId}
            onSuccess={() => setShowCreateForm(false)}
            onCancel={() => setShowCreateForm(false)}
          />
        </div>
      )}

      {assignments?.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 border-2 border-dashed border-slate-200 rounded-xl p-6 dark:border-slate-800">
          <p className="text-slate-500 font-medium dark:text-slate-400 mt-2">
            No assignments created yet
          </p>
          <button 
            onClick={() => setShowCreateForm(true)}
            className="text-sm text-blue-500 hover:text-blue-600 mt-2 hover:underline"
          >
            Create one now
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {assignments?.map((assignment) => (
            <AssignmentItem key={assignment.id} assignment={assignment} />
          ))}
        </div>
      )}
    </div>
  );
}
