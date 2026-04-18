"use client";

import { useAuthStore } from "@/store/authStore";
import { LogOut, LayoutDashboard, FileText,BookOpen } from "lucide-react";
import Link from "next/link";
import { useRouter, usePathname, useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";
import { logoutApi } from "@/lib/api-client";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

type ApiEnvelope<T> = {
  message?: string;
  data: T;
};

type BackendClassHeader = {
  class_id: string;
  name: string;
  class_code?: string | null;
};

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, logout, hydrated } = useAuthStore();
  const hydrateFromStorage = useAuthStore((state) => state.hydrateFromStorage);
  const router = useRouter();
  const pathname = usePathname();
  const params = useParams<{ courseId?: string | string[] }>();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const hydrateFromStorageRef = useRef(hydrateFromStorage);
  const routerRef = useRef(router);

  useEffect(() => {
    hydrateFromStorageRef.current = hydrateFromStorage;
  }, [hydrateFromStorage]);

  useEffect(() => {
    routerRef.current = router;
  }, [router]);

  const courseId = useMemo(() => {
    const raw = params?.courseId;
    if (typeof raw === "string") return raw;
    return undefined;
  }, [params]);

  const courseHeaderQuery = useQuery({
    queryKey: ["dashboard-course-header", courseId],
    enabled: Boolean(courseId),
    staleTime: 30_000,
    queryFn: async () => {
      const res = await apiClient.get<ApiEnvelope<BackendClassHeader>>(
        `/classes/${courseId}`
      );
      return res.data.data;
    },
  });

  const pageTitle = useMemo(() => {
    if (courseId) {
      const classCode = courseHeaderQuery.data?.class_code?.trim();
      const className = courseHeaderQuery.data?.name?.trim();
      return classCode || className || "Course";
    }

    const last = pathname.split("/").pop();
    if (!last || last === "dashboard") 
      return "Dashboard";
    return last.replace("-", " ");
  }, [courseHeaderQuery.data?.class_code, courseHeaderQuery.data?.name, courseId, pathname]);

  // Hydrate auth state once on client mount.
  useEffect(() => {
    hydrateFromStorageRef.current();
  }, []);

  useEffect(() => {
    if (!hydrated) return;

    if (!user) {
      routerRef.current.replace("/login");
    }
  }, [hydrated, user]);

  const handleLogout = useCallback(async () => {
    try {
      await logoutApi();
    } catch {
      // Best-effort: even if server logout fails, clear local session.
    }
    logout();
    
    // Use replace instead of push to avoid showing dashboard in back history
    // If router fails, fall back to direct URL navigation
    try {
      await router.replace("/login");
    } catch {
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
  }, [logout, router]);

  if (!hydrated) {
    return null;
  }

  if (!user) return null;

  const navItems =
    user.role === "teacher"
      ? [
          { name: "Dashboard", href: "/dashboard/teacher", icon: LayoutDashboard },
          { name: "Courses", href: "/dashboard/courses", icon: FileText },
        ]
      : [
          { name: "Dashboard", href: "/dashboard/student", icon: LayoutDashboard },
          { name: "Courses", href: "/dashboard/student", icon: BookOpen },
          { name: "Documents", href: "/dashboard/documents", icon: FileText },
        ];

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900 transition-colors duration-300 dark:bg-slate-950 dark:text-slate-100">
      {/* Mobile sidebar toggle overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-20 bg-slate-900/50 sm:hidden dark:bg-slate-950/80" 
          onClick={() => setSidebarOpen(false)} 
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        "fixed inset-y-0 left-0 z-30 w-64 transform border-r border-slate-200 bg-white transition-transform duration-300 dark:border-slate-800 dark:bg-slate-900 sm:translate-x-0 sm:static",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex h-16 items-center px-6 border-b border-slate-200 dark:border-slate-800">
          <span className="text-lg font-semibold tracking-tight text-slate-800 dark:text-slate-100">LabGuard</span>
        </div>
        
        <div className="flex flex-col justify-between h-[calc(100vh-4rem)] p-4">
          <nav className="flex flex-col gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link 
                  key={item.name}
                  href={item.href} 
                  onClick={() => setSidebarOpen(false)}
                  className={cn(
                    "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:translate-y-[-1px]",
                    isActive 
                      ? "bg-sky-50 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400" 
                      : "text-slate-600 hover:bg-slate-50 hover:text-sky-600 dark:text-slate-400 dark:hover:bg-slate-800/80 dark:hover:text-sky-400"
                  )}
                >
                  <Icon className={cn("h-4 w-4 transition-colors", isActive ? "text-sky-600 dark:text-sky-400" : "text-slate-400 group-hover:text-sky-500")} strokeWidth={1.5} />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1 rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/50">
              <span className="text-sm font-bold text-slate-800 dark:text-slate-200">{user.name}</span>
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider dark:text-slate-400">{user.role}</span>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-all hover:translate-y-[-1px] hover:bg-slate-50 hover:text-red-600 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-red-400"
            >
              <LogOut className="h-4 w-4" strokeWidth={1.5} />
              Logout
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 shrink-0 transition-colors duration-300 dark:bg-slate-900 dark:border-slate-800 sm:px-8">
          <div className="flex items-center gap-4">
            <button 
              className="sm:hidden p-2 -ml-2 text-slate-600 hover:bg-slate-100 rounded-lg dark:text-slate-400 dark:hover:bg-slate-800"
              onClick={() => setSidebarOpen(true)}
            >
              <LayoutDashboard className="h-5 w-5" />
            </button>
            <h1 className="text-xl font-semibold tracking-tight text-slate-800 capitalize dark:text-slate-100">
              {pageTitle}
            </h1>
          </div>
        </header>

        <div className="flex-1 overflow-auto p-4 sm:p-8">
          <div className="mx-auto max-w-5xl">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
