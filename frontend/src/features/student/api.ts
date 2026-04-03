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

type BackendAssignment = {
  id: string;
  class_id: string;
  filename: string;
  description?: string | null;
  due_date?: string | null;
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
    id: a.id,
    courseId: a.class_id,
    title: a.filename,
    description: a.description ?? "",
    dueDate: a.due_date ?? undefined,
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
