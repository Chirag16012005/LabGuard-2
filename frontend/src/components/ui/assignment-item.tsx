"use client";

import { useAuthStore } from "@/store/authStore";
import { useDeleteAssignment } from "@/features/teacher/api";
import { Assignment } from "@/features/teacher/api";
import { AssignmentCard } from "./assignment-card";

interface AssignmentItemProps {
  assignment: Assignment;
}

export function AssignmentItem({ assignment }: AssignmentItemProps) {
  const { user } = useAuthStore();
  const deleteAssignment = useDeleteAssignment();
  
  const isTeacher = user?.role === "teacher";

  const handleDelete = async () => {
    if (window.confirm("Are you sure you want to delete this assignment? This will also delete all student submissions.")) {
      try {
        await deleteAssignment.mutateAsync(assignment.id);
      } catch (error) {
        console.error("Failed to delete assignment:", error);
        alert("Failed to delete assignment. Please try again.");
      }
    }
  };

  return (
    <AssignmentCard
      assignment={assignment}
      href={`/dashboard/course/${assignment.courseId}/assignment/${assignment.id}/submissions`}
      onDelete={isTeacher ? handleDelete : undefined}
    />
  );
}
