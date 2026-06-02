"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { ArrowRight, Loader2, Mail, ShieldCheck } from "lucide-react";

import { forgotPasswordApi } from "@/lib/api-client";
import { useAuthStore } from "@/store/authStore";

export default function ForgotPasswordPage() {
  const router = useRouter();
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

  const [email, setEmail] = useState("");
  const [validationError, setValidationError] = useState("");
  const [success, setSuccess] = useState(false);

  const forgotMutation = useMutation({
    mutationFn: (value: string) => forgotPasswordApi(value),
    onSuccess: () => {
      setSuccess(true);
    },
  });

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setValidationError("");

    const trimmedEmail = email.trim();

    if (!trimmedEmail) {
      setValidationError("Email is required.");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      setValidationError("Please enter a valid email address.");
      return;
    }

    setSuccess(false);
    forgotMutation.mutate(trimmedEmail);
  }

  const errorMessage =
    validationError || (forgotMutation.isError ? forgotMutation.error.message : "");

  if (!hydrated) return null;
  if (user) return null;

  return (
    <div className="w-full max-w-md font-sans">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-blue-100 bg-white shadow-sm">
          <ShieldCheck className="h-7 w-7 text-blue-600" strokeWidth={1.5} />
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-800">
          Forgot your password?
        </h1>
        <p className="mt-1.5 text-sm text-slate-500">
          Enter your email and we’ll send a reset link
        </p>
      </div>

      <div className="rounded-2xl border border-blue-50 bg-white p-6 shadow-sm sm:p-8">
        {errorMessage && (
          <div
            id="forgot-password-error"
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

        {success ? (
          <div
            id="forgot-password-success"
            role="status"
            className="rounded-xl border border-blue-100 bg-[#F0F7FF] px-4 py-3 text-sm text-slate-700"
          >
            If that email exists, a reset link has been sent. Check your inbox.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="email" className="text-sm font-medium text-slate-700">
                Email
              </label>
              <div className="relative">
                <Mail
                  className="pointer-events-none absolute left-3.5 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-slate-400"
                  strokeWidth={1.5}
                />
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={forgotMutation.isPending}
                  className="w-full rounded-xl border border-slate-200 bg-[#F0F7FF] py-2.5 pl-10 pr-4 text-sm text-slate-800 placeholder:text-slate-400 transition-all duration-200 focus:border-blue-400 focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-400 disabled:opacity-60"
                />
              </div>
            </div>

            <button
              id="forgot-password-submit"
              type="submit"
              disabled={forgotMutation.isPending}
              className="group mt-2 flex w-full items-center justify-center gap-2 rounded-xl border-none bg-blue-500 px-4 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:translate-y-[-1px] hover:bg-blue-600 hover:shadow-sm disabled:pointer-events-none disabled:opacity-60"
            >
              {forgotMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Sending link…</span>
                </>
              ) : (
                <>
                  <span>Send reset link</span>
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
