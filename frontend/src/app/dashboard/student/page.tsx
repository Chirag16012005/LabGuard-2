"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BookOpen, Loader2, LogIn, Check, AlertCircle } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { useStudentCourses, useJoinClass } from "@/features/student/api";
import { CourseCard } from "@/components/ui/course-card";

export default function StudentDashboardPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.role !== "student") {
      router.replace("/dashboard/teacher");
    }
  }, [user, router]);

  const { data: courses, isLoading, isError, error } = useStudentCourses();
  const joinMutation = useJoinClass();

  const [joinCode, setJoinCode] = useState("");
  const [joinError, setJoinError] = useState<string | null>(null);
  const [joinSuccess, setJoinSuccess] = useState<string | null>(null);

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault();
    setJoinError(null);
    setJoinSuccess(null);

    const code = joinCode.trim();
    if (!code) {
      setJoinError("Please enter a join code.");
      return;
    }

    try {
      const result = await joinMutation.mutateAsync(code);
      setJoinSuccess(`Joined "${result.name}" successfully!`);
      setJoinCode("");
      setTimeout(() => setJoinSuccess(null), 4000);
    } catch (err) {
      setJoinError(
        err instanceof Error ? err.message : "Failed to join class."
      );
    }
  };

  if (!mounted || !user || user.role !== "student") return null;

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-3">
        <p className="text-red-500 font-medium">
          Failed to load courses
        </p>
        <p className="text-sm text-slate-500">
          {error instanceof Error ? error.message : "Please try again later."}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Welcome back, {user.name}
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 uppercase tracking-wider font-semibold">
          Student Dashboard
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="border border-slate-200 rounded-xl p-5 bg-white dark:bg-slate-900 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <span className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800 text-blue-500">
              <BookOpen className="h-5 w-5" />
            </span>
            <span className="text-sm font-medium text-slate-500 dark:text-slate-400">
              Enrolled Courses
            </span>
          </div>
          <p className="text-3xl font-bold text-slate-900 dark:text-white mt-3">
            {courses?.length ?? 0}
          </p>
        </div>
      </div>

      {/* Join Course */}
      <div className="border border-slate-200 rounded-xl p-5 bg-white dark:bg-slate-900 dark:border-slate-800">
        <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200 mb-3">
          Join a Course
        </h3>
        <form onSubmit={handleJoin} className="flex flex-col sm:flex-row gap-3">
          <input
            id="join-code-input"
            type="text"
            value={joinCode}
            onChange={(e) => {
              setJoinCode(e.target.value.toUpperCase());
              setJoinError(null);
              setJoinSuccess(null);
            }}
            placeholder="Enter classroom join code"
            className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm text-slate-800 placeholder:text-slate-400 font-mono tracking-wider focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition-colors dark:bg-slate-800 dark:border-slate-700 dark:text-slate-200 dark:placeholder:text-slate-500 dark:focus:ring-blue-800 dark:focus:border-blue-600"
          />
          <button
            type="submit"
            disabled={joinMutation.isPending}
            className="flex items-center justify-center gap-2 px-5 py-2 text-sm font-medium text-white bg-slate-900 border border-slate-900 rounded-lg hover:translate-y-[-1px] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-slate-100 dark:text-slate-900 dark:border-slate-100 sm:w-auto"
          >
            {joinMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <LogIn className="h-4 w-4" />
            )}
            Join
          </button>
        </form>

        {/* Success */}
        {joinSuccess && (
          <div className="flex items-center gap-2 mt-3 px-3 py-2 bg-green-50 border border-green-200 rounded-lg dark:bg-green-900/20 dark:border-green-800/50">
            <Check className="h-4 w-4 text-green-600 dark:text-green-400 shrink-0" />
            <span className="text-sm font-medium text-green-700 dark:text-green-300">
              {joinSuccess}
            </span>
          </div>
        )}

        {/* Error */}
        {joinError && (
          <div className="flex items-center gap-2 mt-3 px-3 py-2 bg-red-50 border border-red-200 rounded-lg dark:bg-red-900/20 dark:border-red-800/50">
            <AlertCircle className="h-4 w-4 text-red-500 dark:text-red-400 shrink-0" />
            <span className="text-sm font-medium text-red-600 dark:text-red-300">
              {joinError}
            </span>
          </div>
        )}
      </div>

      {/* Course Grid */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">
          My Courses
        </h2>

        {courses && courses.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {courses.map((course) => (
              <CourseCard
                key={course.id}
                course={course}
                basePath="/dashboard/student/courses"
              />
            ))}
          </div>
        ) : (
          <div className="p-12 border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center text-slate-500 dark:border-slate-800">
            <BookOpen className="h-10 w-10 text-slate-300 dark:text-slate-600 mb-3" />
            <p className="font-medium">No courses yet</p>
            <p className="text-sm mt-1">
              Use the join code above to enroll in your first course.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}