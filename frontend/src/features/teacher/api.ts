import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Course, Assignment } from "@/lib/api";

export type { Assignment } from "@/lib/api";
export type { Course } from "@/lib/api";

type ApiEnvelope<T> = {
  message?: string;
  data: T;
};

type AssignmentReport = {
  report_id?: string;
  assignment_id?: string;
  generated_at?: string | null;
  [key: string]: unknown;
};

export type StudentReportEntry = {
  student_report_id: string;
  report_id?: string;
  assignment_id?: string;
  document_id?: string;
  plagiarism_score?: number;
  comparisons?: unknown;
  [key: string]: unknown;
};

type BackendClass = {
  class_id: string;
  name: string;
  section?: string | null;
  class_code?: string;
  join_code?: string;
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
  // Stored in repo but not in schema
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
export interface CourseStudent {
  id: string;
  fullName: string;
  email: string;
}

// Add this type for the backend response
type BackendStudent = {
  id: string;
  full_name: string;
  email: string;
};
export interface Submission {
  id?: string | null;
  assignmentId: string;
  studentId: string;
  studentName: string;
  status: "submitted" | "processing" | "failed" | "not_submitted";
  submittedAt?: string | null;
  documentId?: string | null;
}

function mapCourse(course: BackendClass): Course {
  return {
    id: course.class_id,
    title: course.name,
    subtitle: [course.class_code, course.section].filter(Boolean).join(" • ") || "Class",
    joinCode: course.join_code,
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

function mapSubmission(submission: BackendSubmission): Submission {
  return {
    id: submission.id,
    assignmentId: submission.assignment_id,
    studentId: submission.student_id,
    studentName: submission.student_name,
    status: submission.status as Submission["status"],
    submittedAt: submission.submitted_at,
    documentId: submission.document_id,
  };
}

// API Functions
export const fetchCourses = async (): Promise<Course[]> => {
  const res = await apiClient.get<ApiEnvelope<BackendClass[]>>("/classes");
  return res.data.data.map(mapCourse);
};

export const fetchCourseById = async (courseId: string): Promise<Course | undefined> => {
  const res = await apiClient.get<ApiEnvelope<BackendClass>>(`/classes/${courseId}`);
  return mapCourse(res.data.data);
};

export const fetchAssignments = async (courseId: string): Promise<Assignment[]> => {
  const res = await apiClient.get<ApiEnvelope<{ class_id: string; assignments: BackendAssignment[] }>>(
    `/classes/${courseId}/assignments`
  );
  return (res.data.data.assignments ?? []).map(mapAssignment);
};

export const fetchAssignmentById = async (assignmentId: string): Promise<Assignment | undefined> => {
  // Response shape: AssignmentDetailResponse => { assignment: AssignmentDetails }
  const res = await apiClient.get<ApiEnvelope<{ assignment: BackendAssignment }>>(
    `/assignments/${assignmentId}`
  );
  return mapAssignment(res.data.data.assignment);
};

export const fetchSubmissions = async (assignmentId: string): Promise<Submission[]> => {
  const res = await apiClient.get<
    ApiEnvelope<{ assignment_id: string; submissions: BackendSubmission[] }>
  >(`/assignments/${assignmentId}/submissions`);
  return (res.data.data.submissions ?? []).map(mapSubmission);
};

export const runPlagiarismCheck = async (assignmentId: string): Promise<unknown> => {
  const res = await apiClient.post<ApiEnvelope<unknown>>(`/detection/run`, {
    assignment_id: assignmentId,
  });
  return res.data.data;
};

export const fetchAssignmentReports = async (assignmentId: string): Promise<AssignmentReport[]> => {
  const res = await apiClient.get<ApiEnvelope<AssignmentReport[]>>(
    `/assignments/${assignmentId}/reports`
  );
  return res.data.data;
};

export const fetchStudentReport = async (studentReportId: string): Promise<StudentReportEntry> => {
  const res = await apiClient.get<ApiEnvelope<StudentReportEntry>>(
    `/reports/student/${studentReportId}`
  );
  return res.data.data;
};

export const getLatestReport = <T extends { generated_at?: string | null }>(reports: T[]): T | undefined => {
  const sorted = [...(reports ?? [])].sort((a, b) => {
    const aParsed = a?.generated_at ? Date.parse(a.generated_at) : 0;
    const bParsed = b?.generated_at ? Date.parse(b.generated_at) : 0;
    const aTime = Number.isFinite(aParsed) ? aParsed : 0;
    const bTime = Number.isFinite(bParsed) ? bParsed : 0;
    return bTime - aTime;
  });
  return sorted[0];
};

export interface CourseStudent {
  id: string;
  fullName: string;
  email: string;
}

export const fetchCourseStudents = async (courseId: string): Promise<CourseStudent[]> => {
  const res = await apiClient.get<ApiEnvelope<{ class_id: string; students: BackendStudent[] }>>(
    `/classes/${courseId}/students`
  );
  return (res.data.data.students ?? []).map((s:BackendStudent) => ({
    id: s.id,
    fullName: s.full_name,
    email: s.email,
  }));
};

export interface CreateAssignmentInput {
  courseId: string;
  title: string;
  description: string;
  dueDate?: string;
  file: File;
}

export const createAssignment = async (data: CreateAssignmentInput): Promise<Assignment> => {
  const formData = new FormData();
  formData.append("file", data.file);
  if (data.description) formData.append("description", data.description);
  if (data.dueDate) formData.append("due_date", data.dueDate);

  // Response shape: AssignmentCreateResponse => { assignment: AssignmentDetails }
  const res = await apiClient.post<ApiEnvelope<{ assignment: BackendAssignment }>>(
    `/classes/${data.courseId}/assignments`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );

  return mapAssignment(res.data.data.assignment);
};

export const deleteAssignment = async (assignmentId: string): Promise<void> => {
  await apiClient.delete(`/assignments/${assignmentId}`);
};

// React Query Hooks
export const useCourses = () => {
  return useQuery({
    queryKey: ["courses"],
    queryFn: fetchCourses,
  });
};

export const useCourse = (courseId: string) => {
    return useQuery({
      queryKey: ["course", courseId],
      queryFn: () => fetchCourseById(courseId),
    });
};

export const useAssignments = (courseId: string) => {
  return useQuery({
    queryKey: ["assignments", courseId],
    queryFn: () => fetchAssignments(courseId),
  });
};

export const useAssignment = (assignmentId: string) => {
    return useQuery({
      queryKey: ["assignment", assignmentId],
      queryFn: () => fetchAssignmentById(assignmentId),
    });
};

export const useSubmissions = (assignmentId: string) => {
  return useQuery({
    queryKey: ["submissions", assignmentId],
    queryFn: () => fetchSubmissions(assignmentId),
  });
};

export const useCourseStudents = (courseId: string) => {
  return useQuery({
    queryKey: ["course-students", courseId],
    queryFn: () => fetchCourseStudents(courseId),
  });
};

export const useCreateAssignment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createAssignment,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["assignments", variables.courseId] });
    },
  });
};

export const useDeleteAssignment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteAssignment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
    },
  });
};

export const useRunPlagiarism = () => {
  return useMutation({
    mutationFn: async (assignmentId: string) => {
      await runPlagiarismCheck(assignmentId);
      const reports = await fetchAssignmentReports(assignmentId);
      return getLatestReport(reports);
    },
  });
};

export const useStudentReport = (studentReportId: string | null | undefined) => {
  return useQuery({
    queryKey: ["student-report", studentReportId],
    queryFn: () => fetchStudentReport(studentReportId as string),
    enabled: Boolean(studentReportId),
  });
};

/* ------------------------------------------------------------------ */
/*  Create Course (Class)                                             */
/* ------------------------------------------------------------------ */

  export interface CreateCoursePayload {
    name: string;
    class_code: string;
    description: string;
    section?: string;
  }

  export interface CreateCourseResult {
    classId: string;
    joinCode: string;
  }

export const createCourse = async (
  data: CreateCoursePayload
): Promise<CreateCourseResult> => {
  // First create the class
  const res = await apiClient.post<ApiEnvelope<{ class_id: string }>>(
    "/classes/",
    {
      name: data.name,
      class_code: data.class_code,
      description: data.description,
      section: data.section || null,
    }
  );

  const classId = res.data.data.class_id;

  // Fetch the created class to get the join_code
  const detail = await apiClient.get<ApiEnvelope<BackendClass & { join_code?: string }>>(
    `/classes/${classId}`
  );

  return {
    classId,
    joinCode: detail.data.data.join_code ?? "",
  };
};

export const useCreateCourse = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createCourse,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courses"] });
    },
  });
};
