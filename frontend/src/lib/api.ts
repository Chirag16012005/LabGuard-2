import { apiClient } from "@/lib/api-client";

type ApiEnvelope<T> = {
  message?: string;
  data: T;
};

type BackendClass = {
  class_id: string;
  name: string;
  section?: string | null;
  class_code?: string;
  join_code?: string;
};

export interface Course {
  id: string;
  title: string;
  subtitle: string;
  joinCode?: string;
}

export interface Assignment {
  id: string;
  courseId: string;
  title: string;
  description: string;
  dueDate?: string;
}

export const getCourses = async (): Promise<Course[]> => {
  const response = await apiClient.get<ApiEnvelope<BackendClass[]>>("/classes/");

  return response.data.data.map((course) => ({
    id: course.class_id,
    title: course.name,
    subtitle: [course.class_code, course.section].filter(Boolean).join(" • ") || "Class",
    joinCode: course.join_code,
  }));
};

export const getCourseById = async (courseId: string): Promise<Course | undefined> => {
  const response = await apiClient.get<ApiEnvelope<BackendClass>>(`/classes/${courseId}`);
  const course = response.data.data;
  return {
    id: course.class_id,
    title: course.name,
    subtitle: [course.class_code, course.section].filter(Boolean).join(" • ") || "Class",
    joinCode: course.join_code,
  };
};

export const getAssignments = async (_courseId: string): Promise<Assignment[]> => {
  void _courseId;
  return [];
};
