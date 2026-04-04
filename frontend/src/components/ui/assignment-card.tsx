"use client";

import { Calendar, FileText, ChevronRight } from "lucide-react";
import Link from "next/link";
import { type Assignment } from "@/lib/api";

interface AssignmentCardProps {
  assignment: Assignment;
  href?: string;
  showIcon?: boolean;
}

export function AssignmentCard({ assignment, href, showIcon = true }: AssignmentCardProps) {
  const content = (
    <div className="border border-slate-200 rounded-xl p-5 hover:translate-y-[-1px] transition-all duration-200 bg-white hover:border-slate-300 flex items-center justify-between group dark:bg-slate-900 dark:border-slate-800 dark:hover:border-slate-700">
      <div className="space-y-2">
        <h4 className="font-semibold text-slate-800 group-hover:text-blue-600 transition-colors dark:text-slate-100 dark:group-hover:text-blue-400">
          {assignment.title}
        </h4>
        {assignment.description && (
          <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-2">
            {assignment.description}
          </p>
        )}
        {assignment.dueDate && (
          <div className="flex items-center gap-1.5 text-sm font-medium text-slate-500 dark:text-slate-400">
            <Calendar className="h-3.5 w-3.5" />
            <span>Due: {new Date(assignment.dueDate).toLocaleDateString()}</span>
          </div>
        )}
      </div>
      <div className="flex items-center gap-4">
        {showIcon && <FileText className="h-5 w-5 text-slate-300 dark:text-slate-600 shrink-0" />}
        {href && <ChevronRight className="h-5 w-5 text-slate-400 group-hover:text-blue-500 transition-colors" />}
      </div>
    </div>
  );

  if (href) {
    return <Link href={href}>{content}</Link>;
  }

  return content;
}
