"use client";

import { useCallback } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

export default function BackButton() {
  const router = useRouter();
  const pathname = usePathname();

  const handleBack = useCallback(() => {
    if (typeof window !== "undefined" && window.history.length > 1) {
      router.back();
      return;
    }

    router.push("/");
  }, [router]);

  if (pathname === "/") return null;

  return (
    <button
      type="button"
      onClick={handleBack}
      aria-label="Go back"
      className="fixed left-4 top-4 z-50 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/95 px-3 py-2 text-sm font-medium text-slate-700 shadow-sm backdrop-blur transition hover:-translate-y-px hover:bg-white hover:text-slate-900 dark:border-slate-700 dark:bg-slate-900/95 dark:text-slate-200 dark:hover:bg-slate-900 dark:hover:text-white"
    >
      <ArrowLeft className="h-4 w-4" />
      Back
    </button>
  );
}
