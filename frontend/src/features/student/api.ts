import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Course, Assignment } from "@/lib/api";

export type { Course, Assignment } from "@/lib/api";

/* ------------------------------------------------------------------ */
/*  Backend response shapes                                           */
/* ------------------------------------------------------------------ */

type ApiEnvelope<T> = {
  message?: string;
  data: T;
};

type BackendClass = {
  class_id: string;
  name: string;
  section?: string | null;
  class_code?: string;
  description?: string | null;
  teacher_id?: string;
  student_count?: number;
};

// Mirrors AssignmentSummary / AssignmentDetails from assignment_schema.py
type BackendAssignment = {
  assignment_id: string;
  class_id: string;
  filename: string;
  content_type: string;
  file_type: "pdf" | "doc" | "docx" | "txt" | "ppt" | "pptx" | "xls" | "xlsx" | "csv" | "image" | "other";
  size_bytes: number;
  status: "draft" | "published" | "closed";
  submission_count: number;
  created_at: string;
  // AssignmentDetails extras
  description?: string | null;
  storage_path?: string | null;
  // Stored in MongoDB but not in strict schema
  due_date?: string | null;
  title?: string | null;
};

type BackendSubmission = {
  id?: string | null;
  assignment_id: string;
  student_id: string;
  student_name: string;
  document_id?: string | null;
  status: "submitted" | "processing" | "failed" | "not_submitted";
  submitted_at?: string | null;
};

/* ------------------------------------------------------------------ */
/*  Mappers                                                           */
/* ------------------------------------------------------------------ */

function mapCourse(c: BackendClass): Course {
  return {
    id: c.class_id,
    title: c.name,
    subtitle:
      [c.class_code, c.section].filter(Boolean).join(" • ") || "Class",
  };
}

function mapAssignment(a: BackendAssignment): Assignment {
  return {
    id: a.assignment_id,
    courseId: a.class_id,
    title: a.title ?? a.filename,
    description: a.description ?? "",
    dueDate: a.due_date ?? undefined,
  };
}

export type Submission = {
  id?: string | null;
  assignmentId: string;
  studentName: string;
  status: "submitted" | "processing" | "failed" | "not_submitted";
  submittedAt?: string | null;
};

function mapSubmission(s: BackendSubmission): Submission {
  return {
    id: s.id,
    assignmentId: s.assignment_id,
    studentName: s.student_name,
    status: s.status,
    submittedAt: s.submitted_at,
  };
}

/* ------------------------------------------------------------------ */
/*  API functions                                                     */
/* ------------------------------------------------------------------ */

export const fetchStudentCourses = async (): Promise<Course[]> => {
  const res = await apiClient.get<ApiEnvelope<BackendClass[]>>("/classes/");
  return res.data.data.map(mapCourse);
};

export const fetchStudentCourseById = async (
  courseId: string
): Promise<Course | undefined> => {
  const res = await apiClient.get<ApiEnvelope<BackendClass>>(
    `/classes/${courseId}`
  );
  return mapCourse(res.data.data);
};

export const fetchStudentAssignments = async (
  courseId: string
): Promise<Assignment[]> => {
  const res = await apiClient.get<
    ApiEnvelope<{ class_id: string; assignments: BackendAssignment[] }>
  >(`/classes/${courseId}/assignments`);
  return (res.data.data.assignments ?? []).map(mapAssignment);
};

/* ------------------------------------------------------------------ */
/*  React Query hooks                                                 */
/* ------------------------------------------------------------------ */

export const useStudentCourses = () =>
  useQuery({
    queryKey: ["student", "courses"],
    queryFn: fetchStudentCourses,
  });

export const useStudentCourse = (courseId: string) =>
  useQuery({
    queryKey: ["student", "course", courseId],
    queryFn: () => fetchStudentCourseById(courseId),
    enabled: !!courseId,
  });

export const useStudentAssignments = (courseId: string) =>
  useQuery({
    queryKey: ["assignments", courseId],
    queryFn: () => fetchStudentAssignments(courseId),
    enabled: !!courseId,
  });

/* ------------------------------------------------------------------ */
/*  Join class by code                                                */
/* ------------------------------------------------------------------ */

export interface JoinClassResult {
  classId: string;
  name: string;
}

export const joinClassByCode = async (
  joinCode: string
): Promise<JoinClassResult> => {
  const res = await apiClient.post<
    ApiEnvelope<{ class_id: string; name: string }>
  >("/classes/join", { join_code: joinCode });
  return {
    classId: res.data.data.class_id,
    name: res.data.data.name,
  };
};

export const useJoinClass = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: joinClassByCode,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student", "courses"] });
    },
  });
};

/* ------------------------------------------------------------------ */
/*  Submit Assignment                                                 */
/* ------------------------------------------------------------------ */

export const submitAssignment = async (
  assignmentId: string,
  file: File
): Promise<Submission> => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await apiClient.post<ApiEnvelope<{ submission_id: string; submission: BackendSubmission }>>(
    `/assignments/${assignmentId}/submit`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );

  // If the backend returns a single submission in 'submission' field
  // or we need to fetch it? The user said "Return: ... submissions: [SubmissionSummary] (or single submission if preferred)"
  // I will assume the backend returns the created submission.
  return mapSubmission(res.data.data.submission);
};

export const useSubmitAssignment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ assignmentId, file }: { assignmentId: string; file: File }) =>
      submitAssignment(assignmentId, file),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["submission", variables.assignmentId],
      });
    },
  });
};

export const fetchStudentSubmission = async (
  assignmentId: string
): Promise<Submission | null> => {
  try {
    const res = await apiClient.get<ApiEnvelope<BackendSubmission>>(
      `/assignments/${assignmentId}/my-submission`
    );
    return mapSubmission(res.data.data);
  } catch (error) {
    return null;
  }
};

export const useStudentSubmission = (assignmentId: string) =>
  useQuery({
    queryKey: ["submission", assignmentId],
    queryFn: () => fetchStudentSubmission(assignmentId),
    enabled: !!assignmentId,
  });
