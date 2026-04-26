"use client";

import { useEffect} from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight, BookOpen, ClipboardCheck, Loader2, Users, AlertCircle } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { useCourses } from "@/features/teacher/api";
import { CourseCard } from "@/components/ui/course-card";

export default function TeacherDashboardPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  // const [mounted, setMounted] = useState(false);
 
  useEffect(() => {
    // setMounted(true);
    // if (mounted) {
      if (!user) {
        router.replace("/login");
        return;
      }
      if (user.role !== "teacher") {
        router.replace("/dashboard/student");
      }
    // }
  }, [user, router]);
 
  const { data: courses, isLoading, isError, error } = useCourses();
 
  if (!user || user.role !== "teacher") 
    return null;

  // Non-blocking render - show content immediately, load courses in background
  const teacherStats = [
    { label: "Active Courses", value: courses?.length || 0, icon: BookOpen, color: "text-blue-500" },
    { label: "Students Enrolled", value: 0, icon: Users, color: "text-green-500" },
    { label: "Pending Submissions", value: 42, icon: ClipboardCheck, color: "text-amber-500" },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Welcome back, {user.name}
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 uppercase tracking-wider font-semibold">
          Teacher Dashboard Overview
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {teacherStats.map((stat) => (
          <div
            key={stat.label}
            className="border border-slate-200 rounded-xl p-5 bg-white dark:bg-slate-900 dark:border-slate-800"
          >
            <div className="flex items-center gap-3">
              <span className={`p-2 rounded-lg bg-slate-50 dark:bg-slate-800 ${stat.color}`}>
                <stat.icon className="h-5 w-5" />
              </span>
              <span className="text-sm font-medium text-slate-500 dark:text-slate-400">
                {stat.label}
              </span>
            </div>
            <p className="text-3xl font-bold text-slate-900 dark:text-white mt-3">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Current Courses</h2>
          <Link
            href="/dashboard/courses"
            className="text-sm font-medium text-blue-500 hover:text-blue-600 flex items-center gap-1 group"
          >
            View all Courses
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>

        {isLoading ? (
          <div className="p-12 border-2 border-dashed border-slate-200 rounded-xl flex items-center justify-center gap-2 text-slate-500 dark:border-slate-800">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Loading courses...</span>
          </div>
        ) : isError ? (
          <div className="p-4 border border-red-200 rounded-xl bg-red-50 dark:bg-red-900/20 dark:border-red-800 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-900 dark:text-red-200">Failed to load courses</p>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error?.message || "Please try refreshing the page"}</p>
            </div>
          </div>
        ) : courses && courses.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {courses.slice(0, 3).map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
        ) : (
          <div className="p-12 border-2 border-dashed border-slate-200 rounded-xl flex items-center justify-center text-slate-500 dark:border-slate-800">
            No courses found. Start by creating your first course.
          </div>
        )}
      </div>
    </div>
  );
}
