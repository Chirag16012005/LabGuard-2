import { Assignment } from "@/features/teacher/api";
import { AssignmentCard } from "./assignment-card";

interface AssignmentItemProps {
  assignment: Assignment;
}

export function AssignmentItem({ assignment }: AssignmentItemProps) {
  return (
    <AssignmentCard
      assignment={assignment}
      href={`/dashboard/course/${assignment.courseId}/assignment/${assignment.id}/submissions`}
    />
  );
}
