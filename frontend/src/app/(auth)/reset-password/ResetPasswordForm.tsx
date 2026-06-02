"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { ArrowRight, Loader2, Lock, ShieldCheck } from "lucide-react";

import { resetPasswordApi } from "@/lib/api-client";
import { useAuthStore } from "@/store/authStore";

type ResetPasswordInput = {
  token: string;
  newPassword: string;
};

export default function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const user = useAuthStore((s) => s.user);
  const hydrated = useAuthStore((s) => s.hydrated);
  const hydrateFromStorage = useAuthStore((s) => s.hydrateFromStorage);
  const hydrateFromStorageRef = useRef(hydrateFromStorage);
  const routerRef = useRef(router);

  useEffect(() => {
    hydrateFromStorageRef.current = hydrateFromStorage;
  }, [hydrateFromStorage]);

  useEffect(() => {
    routerRef.current = router;
  }, [router]);

  useEffect(() => {
    hydrateFromStorageRef.current();
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (user) {
      routerRef.current.replace(
        user.role === "teacher" ? "/dashboard/teacher" : "/dashboard/student"
      );
    }
  }, [hydrated, user]);

  const token = searchParams.get("token");

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [validationError, setValidationError] = useState("");
  const [success, setSuccess] = useState(false);
  const redirectTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (redirectTimeoutRef.current !== null) {
        window.clearTimeout(redirectTimeoutRef.current);
      }
    };
  }, []);

  const resetMutation = useMutation({
    mutationFn: (input: ResetPasswordInput) => resetPasswordApi(input.token, input.newPassword),
    onSuccess: () => {
      setSuccess(true);
      redirectTimeoutRef.current = window.setTimeout(() => {
        router.replace("/login");
      }, 2000);
    },
  });

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setValidationError("");

    if (!token) {
      setValidationError("Invalid reset link.");
      return;
    }

    if (!newPassword.trim()) {
      setValidationError("New password is required.");
      return;
    }

    if (newPassword.length < 6) {
      setValidationError("Password must be at least 6 characters.");
      return;
    }

    if (!confirmPassword.trim()) {
      setValidationError("Please confirm your password.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setValidationError("Passwords do not match.");
      return;
    }

    resetMutation.mutate({ token, newPassword });
  }

  const errorMessage =
    validationError || (resetMutation.isError ? resetMutation.error.message : "");

  if (!hydrated) return null;
  if (user) return null;

  return (
    <div className="w-full max-w-md font-sans">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-blue-100 bg-white shadow-sm">
          <ShieldCheck className="h-7 w-7 text-blue-600" strokeWidth={1.5} />
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-800">
          Reset your password
        </h1>
        <p className="mt-1.5 text-sm text-slate-500">Choose a new password to continue</p>
      </div>

      <div className="rounded-2xl border border-blue-50 bg-white p-6 shadow-sm sm:p-8">
        {errorMessage && (
          <div
            id="reset-password-error"
            role="alert"
            className="mb-5 flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
          >
            <svg className="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 16 16" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M8 15A7 7 0 108 1a7 7 0 000 14zm-.75-4.5a.75.75 0 001.5 0v-4a.75.75 0 00-1.5 0v4zm.75-6.5a.75.75 0 100 1.5.75.75 0 000-1.5z"
                clipRule="evenodd"
              />
            </svg>
            <span>{errorMessage}</span>
          </div>
        )}

        {!token ? (
          <div className="text-sm text-slate-600">
            <p className="mb-4">Invalid reset link.</p>
            <Link
              href="/forgot-password"
              className="font-medium text-blue-600 transition-colors duration-200 hover:text-blue-700"
            >
              Request a new reset link
            </Link>
          </div>
        ) : success ? (
          <div
            id="reset-password-success"
            role="status"
            className="rounded-xl border border-blue-100 bg-[#F0F7FF] px-4 py-3 text-sm text-slate-700"
          >
            Password reset! Redirecting to login...
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="newPassword" className="text-sm font-medium text-slate-700">
                New Password
              </label>
              <div className="relative">
                <Lock
                  className="pointer-events-none absolute left-3.5 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-slate-400"
                  strokeWidth={1.5}
                />
                <input
                  id="newPassword"
                  name="newPassword"
                  type="password"
                  autoComplete="new-password"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  disabled={resetMutation.isPending}
                  className="w-full rounded-xl border border-slate-200 bg-[#F0F7FF] py-2.5 pl-10 pr-4 text-sm text-slate-800 placeholder:text-slate-400 transition-all duration-200 focus:border-blue-400 focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-400 disabled:opacity-60"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="confirmPassword" className="text-sm font-medium text-slate-700">
                Confirm Password
              </label>
              <div className="relative">
                <Lock
                  className="pointer-events-none absolute left-3.5 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-slate-400"
                  strokeWidth={1.5}
                />
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={resetMutation.isPending}
                  className="w-full rounded-xl border border-slate-200 bg-[#F0F7FF] py-2.5 pl-10 pr-4 text-sm text-slate-800 placeholder:text-slate-400 transition-all duration-200 focus:border-blue-400 focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-400 disabled:opacity-60"
                />
              </div>
            </div>

            <button
              id="reset-password-submit"
              type="submit"
              disabled={resetMutation.isPending}
              className="group mt-2 flex w-full items-center justify-center gap-2 rounded-xl border-none bg-blue-500 px-4 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:translate-y-[-1px] hover:bg-blue-600 hover:shadow-sm disabled:pointer-events-none disabled:opacity-60"
            >
              {resetMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Resetting…</span>
                </>
              ) : (
                <>
                  <span>Reset password</span>
                  <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
                </>
              )}
            </button>
          </form>
        )}
      </div>

      <p className="mt-6 text-center text-sm text-slate-500">
        Back to{" "}
        <Link
          href="/login"
          className="font-medium text-blue-600 transition-colors duration-200 hover:text-blue-700"
        >
          Login
        </Link>
      </p>
    </div>
  );
}