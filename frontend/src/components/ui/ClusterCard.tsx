"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { Cluster } from "@/features/teacher/api";

type ClusterCardProps = {
  cluster: Cluster;
  clusterLabel: string;
  memberNames: string[];
};

export default function ClusterCard({ cluster, clusterLabel, memberNames }: ClusterCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const hasHighSimilaritySignal = cluster.size >= 13;

  return (
    <div className="rounded-xl border border-slate-200 bg-white transition-all duration-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
      >
        <div>
          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{clusterLabel}</p>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Number of students: {cluster.size}</p>
        </div>

        <div className="flex items-center gap-2">
          {hasHighSimilaritySignal && (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">
              High similarity
            </span>
          )}
          <ChevronDown
            className={`h-4 w-4 text-slate-500 transition-transform duration-300 ${isOpen ? "rotate-180" : "rotate-0"}`}
          />
        </div>
      </button>

      <div
        className={`overflow-hidden px-4 transition-all duration-300 ease-in-out ${isOpen ? "max-h-80 pb-4 opacity-100" : "max-h-0 pb-0 opacity-0"}`}
      >
        {memberNames.length > 0 ? (
          <ul className="space-y-2 border-t border-slate-100 pt-3 text-sm text-slate-700 dark:border-slate-800 dark:text-slate-200">
            {memberNames.map((name, index) => (
              <li key={`${name}-${index}`} className="rounded-md bg-slate-50 px-3 py-2 dark:bg-slate-800/50">
                {name}
              </li>
            ))}
          </ul>
        ) : (
          <p className="border-t border-slate-100 pt-3 text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400">
            No students found for this cluster.
          </p>
        )}
      </div>
    </div>
  );
}