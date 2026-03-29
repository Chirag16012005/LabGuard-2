import { Assignment } from "@/lib/api";

interface AssignmentItemProps {
  assignment: Assignment;
}

export const AssignmentItem = ({ assignment }: AssignmentItemProps) => {
  const isSubmitted = assignment.status === "submitted";

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border rounded-lg cursor-pointer bg-white border-slate-200 transition-all duration-300 hover:-translate-y-[1px] hover:border-sky-400 hover:shadow-sm dark:bg-slate-900/50 dark:border-slate-800 dark:hover:border-sky-500 gap-4 md:gap-0 dark:hover:shadow-none">
      <div className="flex flex-col">
        <h4 className="font-semibold text-slate-800 dark:text-slate-100 mb-1">{assignment.title}</h4>
        <p className="text-sm text-slate-500 dark:text-slate-400">Due: {assignment.dueDate}</p>
      </div>
      <div className="shrink-0">
        <span
          className={`inline-flex items-center px-3 py-1 text-xs font-medium rounded-md border ${
            isSubmitted
              ? "bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-900/30 dark:text-sky-400 dark:border-sky-800/50"
              : "bg-slate-50 text-slate-600 border-slate-200 dark:bg-slate-800/80 dark:text-slate-400 dark:border-slate-700"
          }`}
        >
          {assignment.status.charAt(0).toUpperCase() + assignment.status.slice(1)}
        </span>
      </div>
    </div>
  );
};
