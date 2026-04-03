"use client";

import { useState } from "react";
import { useCourses, useCreateCourse, CreateCoursePayload } from "@/features/teacher/api";
import { CourseCard } from "@/components/ui/course-card";
import { Loader2, Plus, X, Copy, Check } from "lucide-react";

export default function CoursesPage() {
  const { data: courses, isLoading, isError } = useCourses();
  const createCourseMutation = useCreateCourse();

  const [showForm, setShowForm] = useState(false);
  const [createdJoinCode, setCreatedJoinCode] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const [formData, setFormData] = useState<CreateCoursePayload>({
    name: "",
    class_code: "",
    description: "",
    section: "",
  });

  const [formError, setFormError] = useState<string | null>(null);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setFormError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!formData.name.trim()) {
      setFormError("Course name is required.");
      return;
    }
    if (!formData.class_code.trim()) {
      setFormError("Course code is required.");
      return;
    }
    if (!formData.description.trim()) {
      setFormError("Description is required.");
      return;
    }

    try {
      const result = await createCourseMutation.mutateAsync(formData);
      setCreatedJoinCode(result.joinCode);
      setFormData({ name: "", class_code: "", description: "", section: "" });
    } catch (err) {
      setFormError(
        err instanceof Error ? err.message : "Failed to create course."
      );
    }
  };

  const handleCopyCode = async () => {
    if (!createdJoinCode) return;
    await navigator.clipboard.writeText(createdJoinCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCloseSuccess = () => {
    setCreatedJoinCode(null);
    setShowForm(false);
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-64 items-center justify-center text-red-500">
        Failed to load courses.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Your Courses
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage your classroom and track student progress.
          </p>
        </div>
        {!showForm && !createdJoinCode && (
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-slate-900 border border-slate-900 rounded-lg hover:translate-y-[-1px] transition-all duration-200 dark:bg-slate-100 dark:text-slate-900 dark:border-slate-100"
          >
            <Plus className="h-4 w-4" />
            Create Course
          </button>
        )}
      </div>

      {/* Success — show join code */}
      {createdJoinCode && (
        <div className="border border-green-200 bg-green-50 rounded-xl p-6 dark:bg-green-900/20 dark:border-green-800/50">
          <div className="flex items-start justify-between">
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-green-800 dark:text-green-300">
                Course created successfully!
              </h3>
              <p className="text-sm text-green-700 dark:text-green-400">
                Share this join code with your students so they can enroll:
              </p>
              <div className="flex items-center gap-3">
                <code className="px-4 py-2.5 bg-white border border-green-300 rounded-lg text-lg font-mono font-bold tracking-widest text-green-800 dark:bg-slate-800 dark:border-green-700 dark:text-green-300">
                  {createdJoinCode}
                </code>
                <button
                  onClick={handleCopyCode}
                  className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-green-700 bg-green-100 rounded-lg hover:bg-green-200 transition-colors dark:text-green-300 dark:bg-green-800/40 dark:hover:bg-green-800/60"
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Copy
                    </>
                  )}
                </button>
              </div>
            </div>
            <button
              onClick={handleCloseSuccess}
              className="p-1.5 rounded-lg text-green-600 hover:bg-green-100 transition-colors dark:text-green-400 dark:hover:bg-green-800/40"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}

      {/* Create course form */}
      {showForm && !createdJoinCode && (
        <form
          onSubmit={handleSubmit}
          className="border border-slate-200 rounded-xl p-6 bg-white space-y-5 dark:bg-slate-900 dark:border-slate-800"
        >
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">
              Create New Course
            </h3>
            <button
              type="button"
              onClick={() => {
                setShowForm(false);
                setFormError(null);
              }}
              className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors dark:hover:bg-slate-800 dark:hover:text-slate-300"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label
                htmlFor="create-course-name"
                className="text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                Course Name <span className="text-red-500">*</span>
              </label>
              <input
                id="create-course-name"
                name="name"
                type="text"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="e.g. Data Structures"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition-colors dark:bg-slate-800 dark:border-slate-700 dark:text-slate-200 dark:placeholder:text-slate-500 dark:focus:ring-blue-800 dark:focus:border-blue-600"
              />
            </div>

            <div className="space-y-1.5">
              <label
                htmlFor="create-course-code"
                className="text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                Course Code <span className="text-red-500">*</span>
              </label>
              <input
                id="create-course-code"
                name="class_code"
                type="text"
                value={formData.class_code}
                onChange={handleInputChange}
                placeholder="e.g. CS201"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition-colors dark:bg-slate-800 dark:border-slate-700 dark:text-slate-200 dark:placeholder:text-slate-500 dark:focus:ring-blue-800 dark:focus:border-blue-600"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="create-course-section"
              className="text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Section <span className="text-slate-400">(optional)</span>
            </label>
            <input
              id="create-course-section"
              name="section"
              type="text"
              value={formData.section}
              onChange={handleInputChange}
              placeholder="e.g. Section A"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition-colors dark:bg-slate-800 dark:border-slate-700 dark:text-slate-200 dark:placeholder:text-slate-500 dark:focus:ring-blue-800 dark:focus:border-blue-600"
            />
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="create-course-desc"
              className="text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              id="create-course-desc"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows={3}
              placeholder="Brief description of the course..."
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition-colors resize-none dark:bg-slate-800 dark:border-slate-700 dark:text-slate-200 dark:placeholder:text-slate-500 dark:focus:ring-blue-800 dark:focus:border-blue-600"
            />
          </div>

          {formError && (
            <p className="text-sm text-red-500 font-medium">{formError}</p>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => {
                setShowForm(false);
                setFormError(null);
              }}
              className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800 transition-colors dark:text-slate-400 dark:hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createCourseMutation.isPending}
              className="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-slate-900 rounded-lg hover:translate-y-[-1px] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-slate-100 dark:text-slate-900"
            >
              {createCourseMutation.isPending && (
                <Loader2 className="h-4 w-4 animate-spin" />
              )}
              Create Course
            </button>
          </div>
        </form>
      )}

      {/* Course grid */}
      {!courses || courses.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-slate-500 border-2 border-dashed border-slate-200 rounded-xl dark:border-slate-800">
          <p className="font-medium">No courses available.</p>
          {!showForm && (
            <button
              onClick={() => setShowForm(true)}
              className="text-sm text-blue-500 hover:text-blue-600 mt-2 hover:underline"
            >
              Create your first course
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      )}
    </div>
  );
}
