"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuthStore } from "@/store/authStore";

export default function DashboardRedirectPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    if (!user) {
      router.replace("/login");
      return;
    }
    router.replace(user.role === "teacher" ? "/dashboard/teacher" : "/dashboard/student");
  }, [user, router]);

  return null;
}
