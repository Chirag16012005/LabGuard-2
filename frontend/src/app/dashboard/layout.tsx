"use client";

import { useAuthStore } from "@/store/use-auth-store";
import { LogOut, LayoutDashboard, FileText, Activity } from "lucide-react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (!user) {
      router.push("/login");
    }
  }, [user, router]);

  if (!mounted || !user) return null;

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Documents", href: "/dashboard/documents", icon: FileText },
    { name: "Reports", href: "/dashboard/reports", icon: Activity },
  ];

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      {/* Mobile sidebar toggle overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-20 bg-slate-900/50 sm:hidden" 
          onClick={() => setSidebarOpen(false)} 
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        "fixed inset-y-0 left-0 z-30 w-64 transform border-r border-slate-200 bg-white transition-transform sm:translate-x-0 sm:static",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex h-16 items-center px-6 border-b border-slate-200">
          <span className="text-lg font-semibold tracking-tight text-slate-900">LabGuard</span>
        </div>
        
        <div className="flex flex-col justify-between h-[calc(100vh-4rem)] p-4">
          <nav className="flex flex-col gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link 
                  key={item.href}
                  href={item.href} 
                  onClick={() => setSidebarOpen(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:translate-y-[-2px]",
                    isActive 
                      ? "bg-slate-100 text-slate-900" 
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  )}
                >
                  <Icon className={cn("h-4 w-4", isActive ? "text-slate-700" : "text-slate-400")} strokeWidth={1.5} />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <span className="text-sm font-bold text-slate-900">{user.name}</span>
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{user.role}</span>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-red-600 transition-all hover:translate-y-[-2px] hover:bg-red-50 hover:text-red-700"
            >
              <LogOut className="h-4 w-4" strokeWidth={1.5} />
              Logout
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-8">
          <div className="flex items-center gap-4">
            <button 
              className="sm:hidden p-2 -ml-2 text-slate-600 hover:bg-slate-100 rounded-lg"
              onClick={() => setSidebarOpen(true)}
            >
              <LayoutDashboard className="h-5 w-5" />
            </button>
            <h1 className="text-xl font-semibold tracking-tight text-slate-900 capitalize">
              {pathname.split('/').pop() === 'dashboard' ? 'Dashboard' : pathname.split('/').pop()?.replace('-', ' ')}
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
