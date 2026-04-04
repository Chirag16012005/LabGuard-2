import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Course, Assignment } from "@/lib/api";

export type { Assignment } from "@/lib/api";
export type { Course } from "@/lib/api";

type ApiEnvelope<T> = {
  message?: string;
  data: T;
};

type BackendClass = {
  class_id: string;
  name: string;
  section?: string | null;
  class_code?: string;
};

type BackendAssignment = {
  id: string;
  class_id: string;
  filename: string;
  description?: string | null;
};

type BackendSubmission = {
  id: string;
  assignment_id: string;
  student_id: string;
  status: "submitted" | "processing" | "failed";
  submitted_at?: string;
};

export interface Submission {
  id: string;
  assignmentId: string;
  studentName: string;
  status: "submitted" | "not_submitted";
  submittedAt?: string;
}

function mapCourse(course: BackendClass): Course {
  return {
    id: course.class_id,
    title: course.name,
    subtitle: [course.class_code, course.section].filter(Boolean).join(" • ") || "Class",
  };
}

function mapAssignment(assignment: BackendAssignment): Assignment {
  return {
    id: assignment.id,
    courseId: assignment.class_id,
    title: assignment.filename,
    description: assignment.description ?? "",
  };
}

function mapSubmission(submission: BackendSubmission): Submission {
  return {
    id: submission.id,
    assignmentId: submission.assignment_id,
    studentName: submission.student_id,
    status: submission.status === "submitted" ? "submitted" : "not_submitted",
    submittedAt: submission.submitted_at,
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

export const createAssignment = async (data: Omit<Assignment, "id">): Promise<Assignment> => {
  const res = await apiClient.post<
    ApiEnvelope<{ assignment: BackendAssignment }>
  >(`/classes/${data.courseId}/assignments`, {
    filename: data.title,
    content_type: "application/pdf",
    size_bytes: 1,
    file_type: "pdf",
    description: data.description,
  });

  return mapAssignment(res.data.data.assignment);
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

export const useCreateAssignment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createAssignment,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["assignments", variables.courseId] });
    },
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
