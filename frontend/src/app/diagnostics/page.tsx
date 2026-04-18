"use client";

import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle, Clock, Zap } from "lucide-react";

interface DiagnosticResult {
  name: string;
  status: "success" | "warning" | "error";
  duration?: number;
  message: string;
}

export default function DiagnosticsPage() {
  const [results, setResults] = useState<DiagnosticResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const runDiagnostics = async () => {
      const diagnostics: DiagnosticResult[] = [];
      const startTime = performance.now();

      // Test 1: Check API connectivity
      console.log("[DIAG] Testing API connectivity...");
      const apiStart = performance.now();
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001/api/v1"}/health`,
          { signal: AbortSignal.timeout(5000) }
        );
        const apiDuration = performance.now() - apiStart;
        if (response.ok) {
          diagnostics.push({
            name: "Backend API",
            status: "success",
            duration: Math.round(apiDuration),
            message: `Connected successfully (${Math.round(apiDuration)}ms)`,
          });
        } else {
          diagnostics.push({
            name: "Backend API",
            status: "error",
            duration: Math.round(apiDuration),
            message: `HTTP ${response.status} - Backend may be misconfigured`,
          });
        }
      } catch (error) {
        const apiDuration = performance.now() - apiStart;
        diagnostics.push({
          name: "Backend API",
          status: "error",
          duration: Math.round(apiDuration),
          message: `Failed to connect (${error instanceof Error ? error.message : "Unknown error"})`,
        });
      }

      // Test 2: Check localStorage
      console.log("[DIAG] Testing localStorage...");
      const storageStart = performance.now();
      try {
        localStorage.setItem("_test", "1");
        localStorage.removeItem("_test");
        const storageDuration = performance.now() - storageStart;
        diagnostics.push({
          name: "localStorage",
          status: "success",
          duration: Math.round(storageDuration),
          message: `Working (${Math.round(storageDuration)}ms)`,
        });
      } catch {
        diagnostics.push({
          name: "localStorage",
          status: "error",
          message: "Failed - may affect auth persistence",
        });
      }

      // Test 3: Check Query Client
      console.log("[DIAG] Testing Query Client...");
      const queryStart = performance.now();
      try {
        const { getQueryClient } = await import("@/lib/react-query");
        const client = getQueryClient();
        const queryDuration = performance.now() - queryStart;
        diagnostics.push({
          name: "React Query",
          status: "success",
          duration: Math.round(queryDuration),
          message: `Initialized (${Math.round(queryDuration)}ms)`,
        });
      } catch (error) {
        diagnostics.push({
          name: "React Query",
          status: "error",
          message: `Failed to initialize (${error instanceof Error ? error.message : "Unknown error"})`,
        });
      }

      // Test 4: Auth Store
      console.log("[DIAG] Testing Auth Store...");
      const authStart = performance.now();
      try {
        const { useAuthStore } = await import("@/store/authStore");
        const store = useAuthStore();
        const authDuration = performance.now() - authStart;
        diagnostics.push({
          name: "Auth Store (Zustand)",
          status: "success",
          duration: Math.round(authDuration),
          message: `Loaded (${Math.round(authDuration)}ms) - user: ${store.user?.email || "none"}`,
        });
      } catch (error) {
        diagnostics.push({
          name: "Auth Store",
          status: "error",
          message: `Failed (${error instanceof Error ? error.message : "Unknown error"})`,
        });
      }

      const totalTime = performance.now() - startTime;
      console.log(`[DIAG] Total diagnostic time: ${Math.round(totalTime)}ms`);

      setResults(diagnostics);
      setIsLoading(false);
    };

    runDiagnostics();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-8">
      <div className="mx-auto max-w-3xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
            LabGuard Diagnostics
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Check your frontend and backend configuration
          </p>
        </div>

        {isLoading ? (
          <div className="p-8 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 flex items-center gap-3 justify-center">
            <div className="animate-spin">
              <Zap className="h-5 w-5 text-blue-500" />
            </div>
            <span className="text-slate-600 dark:text-slate-400">Running diagnostics...</span>
          </div>
        ) : (
          <div className="space-y-4">
            {results.map((result, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-lg border ${
                  result.status === "success"
                    ? "bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800"
                    : result.status === "warning"
                      ? "bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800"
                      : "bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800"
                }`}
              >
                <div className="flex items-start gap-3">
                  {result.status === "success" ? (
                    <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                  ) : result.status === "warning" ? (
                    <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <h3
                      className={`font-semibold ${
                        result.status === "success"
                          ? "text-green-900 dark:text-green-200"
                          : result.status === "warning"
                            ? "text-yellow-900 dark:text-yellow-200"
                            : "text-red-900 dark:text-red-200"
                      }`}
                    >
                      {result.name}
                    </h3>
                    <p
                      className={`text-sm mt-1 ${
                        result.status === "success"
                          ? "text-green-800 dark:text-green-300"
                          : result.status === "warning"
                            ? "text-yellow-800 dark:text-yellow-300"
                            : "text-red-800 dark:text-red-300"
                      }`}
                    >
                      {result.message}
                    </p>
                    {result.duration !== undefined && (
                      <div className="flex items-center gap-1 mt-2 text-xs text-slate-600 dark:text-slate-400">
                        <Clock className="h-3 w-3" />
                        <span>{result.duration}ms</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
                Next Steps
              </h3>
              <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1 list-disc list-inside">
                <li>Check browser console (F12) for [API] and [DIAG] logs</li>
                <li>Verify backend is running: <code className="bg-blue-100 dark:bg-blue-900 px-2 py-1 rounded">curl http://localhost:8001/api/v1/health</code></li>
                <li>Check Network tab in DevTools for slow requests</li>
                <li>Run: <code className="bg-blue-100 dark:bg-blue-900 px-2 py-1 rounded">npm run build</code> to check build performance</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
