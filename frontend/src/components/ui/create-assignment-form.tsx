import React, { useState } from "react";
import { useCreateAssignment } from "@/features/teacher/api";
import type { CreateAssignmentInput } from "@/features/teacher/api";
import { FileInput } from "./file-input";
import { Loader2 } from "lucide-react";

interface CreateAssignmentFormProps {
  courseId: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function CreateAssignmentForm({ courseId, onSuccess, onCancel }: CreateAssignmentFormProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const { mutate, isPending } = useCreateAssignment();

  const isSubmitDisabled = !title.trim() || !description.trim() || !file || isPending;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitDisabled || !file) return;

    const payload: CreateAssignmentInput = {
      courseId,
      title,
      description,
      dueDate: dueDate || undefined,
      file,
    };

    mutate(payload, {
      onSuccess: () => {
        setTitle("");
        setDescription("");
        setDueDate("");
        setFile(null);
        onSuccess?.();
      },
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1">
        <label htmlFor="title" className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Assignment Title <span className="text-red-500">*</span>
        </label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Essay 1"
          className="w-full border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow dark:bg-slate-900/50 dark:border-slate-700 dark:text-slate-100 dark:focus:ring-blue-600"
          required
        />
      </div>

      <div className="space-y-1">
        <label htmlFor="description" className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Description <span className="text-red-500">*</span>
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
          placeholder="Detailed instructions..."
          className="w-full border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow resize-none dark:bg-slate-900/50 dark:border-slate-700 dark:text-slate-100 dark:focus:ring-blue-600"
          required
        />
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Due Date
        </label>
        <input
          type="date"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
          className="w-full border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow dark:bg-slate-900/50 dark:border-slate-700 dark:text-slate-100 dark:focus:ring-blue-600"
        />
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Upload PDF <span className="text-red-500">*</span>
        </label>
        <FileInput onFileChange={(f) => setFile(f)} accept=".pdf" />
        {!file && (
          <p className="text-xs text-red-500 mt-1">A PDF file is required.</p>
        )}
      </div>

      <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-200 mt-6 dark:border-slate-800">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isPending}
            className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors disabled:opacity-50 dark:text-slate-400 dark:hover:text-slate-200"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={isSubmitDisabled}
          className="flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-slate-900 border border-slate-900 rounded-xl hover:translate-y-[-1px] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 dark:bg-slate-100 dark:text-slate-900 dark:border-slate-100"
        >
          {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
          {isPending ? "Creating..." : "Create Assignment"}
        </button>
      </div>
    </form>
  );
}
