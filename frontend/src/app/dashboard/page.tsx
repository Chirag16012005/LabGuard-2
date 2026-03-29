"use client";

import { useAuthStore } from "@/store/authStore";
import { useCourses } from "@/features/courses/api/get-courses";
import { CourseCard } from "@/components/ui/course-card";

export default function DashboardPage() {
  const { role } = useAuthStore();
  
  const { data: courses, isLoading, error } = useCourses();

  if (role !== "student") {
    return (
      <div className="p-6 md:p-8 max-w-7xl mx-auto">
        <p className="text-slate-500 dark:text-slate-400">
          Only students can view the courses dashboard.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto min-h-screen">
      <h1 className="text-2xl font-bold mb-6 text-slate-800 dark:text-slate-100">Courses</h1>

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Skeleton Loaders */}
          {[1, 2, 3].map((skeleton) => (
            <div
              key={skeleton}
              className="bg-slate-100 dark:bg-slate-800/80 animate-pulse border border-slate-200 dark:border-slate-800 rounded-xl p-5 h-[132px]"
            />
          ))}
        </div>
      )}

      {error && (
        <div className="text-red-500 dark:text-red-400">Failed to load courses.</div>
      )}

      {!isLoading && !error && courses?.length === 0 && (
        <div className="flex items-center justify-center p-12 border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-900/50">
          <p className="text-slate-500 dark:text-slate-400">No courses available</p>
        </div>
      )}

      {!isLoading && !error && courses && courses.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      )}
    </div>
  );
}
