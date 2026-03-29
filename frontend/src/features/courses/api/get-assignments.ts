import { useQuery } from '@tanstack/react-query';
import { getAssignments, Assignment } from '@/lib/api';

export type { Assignment };

export const useAssignments = (courseId: string) => {
  return useQuery({
    queryKey: ['assignments', courseId],
    queryFn: () => getAssignments(courseId),
    enabled: !!courseId,
  });
};
