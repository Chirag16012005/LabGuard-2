"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  KeyRound,
  Loader2,
  Mail,
  ShieldUser,
  UserCircle2,
} from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { changePasswordApi, logoutApi } from "@/lib/api-client";
import { fetchCourses } from "@/features/teacher/api";
import { fetchStudentCourses } from "@/features/student/api";

export default function ProfilePage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      router.replace("/login");
    }
  }, [router, user]);

  const isTeacher = user?.role === "teacher";
  const isStudent = user?.role === "student";

  const teacherCoursesQuery = useQuery({
    queryKey: ["profile", "teacher-courses-count"],
    queryFn: fetchCourses,
    enabled: isTeacher,
    staleTime: 60_000,
  });

  const studentCoursesQuery = useQuery({
    queryKey: ["profile", "student-courses-count"],
    queryFn: fetchStudentCourses,
    enabled: isStudent,
    staleTime: 60_000,
  });

  const courseCount = isTeacher
    ? teacherCoursesQuery.data?.length ?? 0
    : studentCoursesQuery.data?.length ?? 0;

  const courseLabel = isTeacher
    ? "No. of courses you teach"
    : "No. of courses you are involved in";

  const isCoursesLoading = isTeacher
    ? teacherCoursesQuery.isLoading
    : studentCoursesQuery.isLoading;

  const changePasswordMutation = useMutation({
    mutationFn: changePasswordApi,
    onSuccess: async () => {
      setSuccessMessage("Password changed successfully. Please log in again.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");

      try {
        await logoutApi();
      } catch {
        // Best effort; local logout still happens.
      }

      logout();
      router.replace("/login");
    },
  });

  const roleTitle = useMemo(() => {
    if (isTeacher) return "Teacher Profile";
    if (isStudent) return "Student Profile";
    return "Profile";
  }, [isStudent, isTeacher]);

  const handleChangePassword = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);
    setSuccessMessage(null);

    if (!currentPassword || !newPassword || !confirmPassword) {
      setFormError("All password fields are required.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setFormError("New password and confirm password do not match.");
      return;
    }

    if (currentPassword === newPassword) {
      setFormError("New password must be different from current password.");
      return;
    }

    changePasswordMutation.mutate({
      currentPassword,
      newPassword,
    });
  };

  if (!user) {
    return null;
  }

  return (
    <div className="space-y-8">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-8">
        <div className="mb-8 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              {roleTitle}
            </h1>
            <p className="mt-1 text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Manage your account details
            </p>
          </div>
          <div className="rounded-xl border border-sky-100 bg-sky-50 p-2.5 dark:border-sky-900/50 dark:bg-sky-900/30">
            <UserCircle2 className="h-7 w-7 text-sky-600 dark:text-sky-300" />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/50">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Full Name
            </p>
            <p className="mt-2 text-base font-semibold text-slate-900 dark:text-slate-100">
              {user.name}
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/50">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Email ID
            </p>
            <p className="mt-2 flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-slate-100">
              <Mail className="h-4 w-4 text-slate-500" />
              <span className="truncate">{user.email}</span>
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/50">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              {courseLabel}
            </p>
            <p className="mt-2 flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-slate-100">
              <BookOpen className="h-4 w-4 text-slate-500" />
              {isCoursesLoading ? (
                <span className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 dark:text-slate-400">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading...
                </span>
              ) : (
                <span>{courseCount}</span>
              )}
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-8">
        <div className="mb-5 flex items-center gap-3">
          <div className="rounded-lg bg-slate-100 p-2 dark:bg-slate-800">
            <KeyRound className="h-5 w-5 text-slate-700 dark:text-slate-200" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Change Password
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Update your password to keep your account secure.
            </p>
          </div>
        </div>

        <form className="space-y-4" onSubmit={handleChangePassword}>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-1.5">
              <label
                htmlFor="currentPassword"
                className="text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                Current Password
              </label>
              <input
                id="currentPassword"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-sky-500 dark:focus:ring-sky-900/40"
                placeholder="Enter current password"
                autoComplete="current-password"
              />
            </div>

            <div className="space-y-1.5">
              <label
                htmlFor="newPassword"
                className="text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                New Password
              </label>
              <input
                id="newPassword"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-sky-500 dark:focus:ring-sky-900/40"
                placeholder="Enter new password"
                autoComplete="new-password"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="confirmPassword"
              className="text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Confirm New Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-sky-500 dark:focus:ring-sky-900/40"
              placeholder="Re-enter new password"
              autoComplete="new-password"
            />
          </div>

          {(formError || changePasswordMutation.isError) && (
            <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{formError ?? changePasswordMutation.error.message}</span>
            </div>
          )}

          {successMessage && (
            <div className="flex items-start gap-2 rounded-lg border border-green-200 bg-green-50 px-3 py-2.5 text-sm text-green-700 dark:border-green-800 dark:bg-green-900/20 dark:text-green-300">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}

          <div className="flex items-center justify-between gap-3 pt-2">
            <p className="inline-flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
              <ShieldUser className="h-4 w-4" />
              Secure account settings
            </p>
            <button
              type="submit"
              disabled={changePasswordMutation.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:translate-y-[-1px] hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
            >
              {changePasswordMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <KeyRound className="h-4 w-4" />
              )}
              Change Password
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
