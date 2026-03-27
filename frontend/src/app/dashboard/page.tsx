"use client";

import { useAuthStore } from "@/store/use-auth-store";
import { useQuery } from "@tanstack/react-query";
import { FileText, Upload, AlertTriangle, Users } from "lucide-react";
import { useRouter } from "next/navigation";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

// Reusable UI Components
function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("rounded-xl border border-slate-200 bg-white p-4 transition-transform hover:translate-y-[-2px]", className)}>
      {children}
    </div>
  );
}

function Badge({ children, variant = "default", className }: { children: React.ReactNode; variant?: "default" | "danger" | "warning" | "success"; className?: string }) {
  const variants = {
    default: "bg-slate-100 text-slate-700 border-slate-200",
    danger: "bg-red-50 text-red-700 border-red-200",
    warning: "bg-amber-50 text-amber-700 border-amber-200",
    success: "bg-emerald-50 text-emerald-700 border-emerald-200",
  };
  return (
    <span className={cn("inline-flex items-center rounded-lg border px-2.5 py-0.5 text-xs font-semibold tracking-wide", variants[variant], className)}>
      {children}
    </span>
  );
}

function Button({ children, onClick, variant = "primary", className, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "outline" | "danger" }) {
  const variants = {
    primary: "bg-slate-900 text-white hover:bg-slate-800 border-slate-900",
    secondary: "bg-slate-100 text-slate-900 hover:bg-slate-200 border-transparent",
    outline: "bg-white text-slate-700 hover:bg-slate-50 border-slate-200",
    danger: "bg-red-50 text-red-700 hover:bg-red-100 border-red-200",
  };
  return (
    <button
      onClick={onClick}
      className={cn("inline-flex items-center justify-center rounded-lg border px-4 py-2 text-sm font-medium transition-all hover:translate-y-[-2px]", variants[variant], className)}
      {...props}
    >
      {children}
    </button>
  );
}

// Mock API Call
const fetchDashboardData = async (role: "student" | "teacher" | undefined) => {
  if (!role) return null;
  return new Promise<any>((resolve) => {
    setTimeout(() => {
      if (role === "student") {
        resolve({
          recentSubmissions: [
            { id: "1", title: "History Essay Draft 1", date: "2026-03-25", score: 12 },
            { id: "2", title: "Science Lab Report v2", date: "2026-03-22", score: 4 },
            { id: "3", title: "Term Paper Reference", date: "2026-03-15", score: 38 },
          ],
        });
      } else {
        resolve({
          classrooms: [
            { id: "c1", name: "Biology 101", students: 24, submissions: 12 },
            { id: "c2", name: "World History", students: 30, submissions: 28 },
          ],
          alerts: [
            { id: "a1", student: "Alice Smith", document: "Final Essay", score: 85, date: "2026-03-26" },
            { id: "a2", student: "Bob Jones", document: "Lab Report 3", score: 62, date: "2026-03-25" },
          ],
          recentSubmissions: [
            { id: "s1", student: "Charlie Brown", title: "Unit 4 Homework", date: "2026-03-27", score: 5 },
            { id: "s2", student: "Diana Prince", title: "Unit 4 Homework", date: "2026-03-27", score: 12 },
          ]
        });
      }
    }, 800);
  });
};

export default function DashboardPage() {
  const { user } = useAuthStore();
  const router = useRouter();

  const { data, isLoading } = useQuery({
    queryKey: ["dashboardData", user?.role],
    queryFn: () => fetchDashboardData(user?.role as ("student" | "teacher")),
    enabled: !!user,
  });

  if (!user) return null;

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-900"></div>
      </div>
    );
  }

  return user.role === "student" ? <StudentDashboard data={data} router={router} /> : <TeacherDashboard data={data} router={router} />;
}

// Student View
function StudentDashboard({ data, router }: { data: any, router: any }) {
  const getBadgeVariant = (score: number) => {
    if (score < 15) return "success";
    if (score < 40) return "warning";
    return "danger";
  };

  return (
    <div className="space-y-8">
      {/* Upload CTA Card */}
      <Card className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-50 border-dashed border-2 p-6 hover:translate-y-0">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-slate-900">Check a new document</h2>
          <p className="mt-1 text-sm text-slate-600">Upload your latest draft to intelligently scan for similarity against millions of sources.</p>
        </div>
        <Button onClick={() => router.push("/dashboard/documents/upload")} className="w-full sm:w-auto shrink-0 gap-2 px-6">
          <Upload className="h-4 w-4" />
          Upload Document
        </Button>
      </Card>

      {/* Submissions List */}
      <div>
        <h2 className="mb-4 text-lg font-semibold tracking-tight text-slate-900">Recent Submissions</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data?.recentSubmissions?.map((sub: any) => (
            <Card key={sub.id} className="flex flex-col justify-between p-5">
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-2">
                    <FileText className="h-4 w-4 text-slate-600" />
                  </div>
                  <Badge variant={getBadgeVariant(sub.score)}>{sub.score}% Match</Badge>
                </div>
                <h3 className="font-semibold text-slate-900 line-clamp-1">{sub.title}</h3>
                <p className="mt-1 text-xs text-slate-500 font-medium">{sub.date}</p>
              </div>
              <Button variant="outline" className="mt-5 w-full">View Full Report</Button>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

// Teacher View
function TeacherDashboard({ data, router }: { data: any, router: any }) {
  return (
    <div className="space-y-10">
      {/* Alerts */}
      {data?.alerts?.length > 0 && (
        <section>
          <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold tracking-tight text-slate-900">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            High Plagiarism Alerts
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {data.alerts.map((alert: any) => (
              <Card key={alert.id} className="border-red-200 bg-red-50 hover:bg-red-100/50 p-5">
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <h3 className="font-semibold tracking-tight text-slate-900">{alert.student}</h3>
                    <p className="mt-1 text-sm font-medium text-slate-700">{alert.document}</p>
                    <p className="mt-2 text-xs text-slate-500">{alert.date}</p>
                  </div>
                  <Badge variant="danger" className="text-sm px-3 py-1 shrink-0">{alert.score}% Match</Badge>
                </div>
                <Button variant="danger" className="mt-5 w-full">Review Submission</Button>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Overview Grid */}
      <div className="grid gap-8 lg:grid-cols-3">
        {/* Classrooms */}
        <section className="lg:col-span-1">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-tight text-slate-900">Classrooms</h2>
            <Button variant="outline" className="px-3 py-1.5 text-xs font-semibold">+ New</Button>
          </div>
          <div className="space-y-4">
            {data?.classrooms?.map((cls: any) => (
              <Card key={cls.id} className="cursor-pointer p-4">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-slate-700">
                    <Users className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">{cls.name}</h3>
                    <p className="mt-1 text-xs font-medium text-slate-500">
                      {cls.students} Students • {cls.submissions} Submissions
                    </p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </section>

        {/* Recent Submissions */}
        <section className="lg:col-span-2">
           <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-tight text-slate-900">Recent Submissions</h2>
            <Button variant="outline" className="px-3 py-1.5 text-xs font-semibold">View All</Button>
          </div>
          <div className="space-y-4">
            {data?.recentSubmissions?.map((sub: any) => (
              <Card key={sub.id} className="flex items-center justify-between p-4">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-slate-700">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">{sub.title}</h3>
                    <p className="mt-1 text-xs font-medium text-slate-500">{sub.student} • {sub.date}</p>
                  </div>
                </div>
                <Badge variant={sub.score > 20 ? (sub.score > 40 ? "danger" : "warning") : "success"}>
                  {sub.score}%
                </Badge>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
