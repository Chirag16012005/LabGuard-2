"use client";

import { useEffect, useRef, useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { ArrowRight, Loader2, Lock, Mail, ShieldCheck } from "lucide-react";

import { loginApi } from "@/lib/api-client";
import { useAuthStore } from "@/store/authStore";
import { LoginCredentials } from "@/types/auth";

export default function LoginPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const hydrated = useAuthStore((s) => s.hydrated);
  const hydrateFromStorage = useAuthStore((s) => s.hydrateFromStorage);
  const setUser = useAuthStore((s) => s.setUser);
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
  const [password, setPassword] = useState("");
  const [validationError, setValidationError] = useState("");

  const loginMutation = useMutation({
    mutationFn: (credentials: LoginCredentials) => loginApi(credentials),
    onSuccess: (data) => {
      setUser(data.user, data.token);
      router.push(data.user.role === "teacher" ? "/dashboard/teacher" : "/dashboard/student");
    },
  });

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setValidationError("");

    if (!email.trim()) {
      setValidationError("Email is required.");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setValidationError("Please enter a valid email address.");
      return;
    }

    if (!password.trim()) {
      setValidationError("Password is required.");
      return;
    }

    loginMutation.mutate({ email, password });
  }

  const errorMessage = validationError || (loginMutation.isError ? loginMutation.error.message : "");

  if (!hydrated) return null;
  if (user) return null;

  return (
    <div className="w-full max-w-md font-sans">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-blue-100 bg-white shadow-sm">
          <ShieldCheck className="h-7 w-7 text-blue-600" strokeWidth={1.5} />
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-800">Welcome back</h1>
        <p className="mt-1.5 text-sm text-slate-500">Sign in to continue to LabGuard</p>
      </div>

      <div className="rounded-2xl border border-blue-50 bg-white p-6 shadow-sm sm:p-8">
        {errorMessage && (
          <div
            id="login-error"
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
                className="w-full rounded-xl border border-slate-200 bg-[#F0F7FF] py-2.5 pl-10 pr-4 text-sm text-slate-800 placeholder:text-slate-400 transition-all duration-200 focus:border-blue-400 focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-400"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="password" className="text-sm font-medium text-slate-700">
              Password
            </label>
            <div className="relative">
              <Lock
                className="pointer-events-none absolute left-3.5 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-slate-400"
                strokeWidth={1.5}
              />
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-[#F0F7FF] py-2.5 pl-10 pr-4 text-sm text-slate-800 placeholder:text-slate-400 transition-all duration-200 focus:border-blue-400 focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-400"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <Link
              href="/forgot-password"
              className="text-xs font-medium text-slate-500 transition-colors duration-200 hover:text-slate-700"
            >
              Forgot your password?
            </Link>
          </div>

          <button
            id="login-submit"
            type="submit"
            disabled={loginMutation.isPending}
            className="group mt-2 flex w-full items-center justify-center gap-2 rounded-xl border-none bg-blue-500 px-4 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:translate-y-[-1px] hover:bg-blue-600 hover:shadow-sm disabled:pointer-events-none disabled:opacity-60"
          >
            {loginMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Signing in…</span>
              </>
            ) : (
              <>
                <span>Sign in</span>
                <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
              </>
            )}
          </button>
        </form>
      </div>

      <p className="mt-6 text-center text-sm text-slate-500">
        Don’t have an account?{" "}
        <Link href="/register" className="font-medium text-blue-600 transition-colors duration-200 hover:text-blue-700">
          Create one
        </Link>
      </p>
    </div>
  );
}
