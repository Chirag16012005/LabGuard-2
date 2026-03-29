import { useQuery } from '@tanstack/react-query';
import { getCourses, Course } from '@/lib/api';

export type { Course };

export const useCourses = () => {
  return useQuery({
    queryKey: ['courses'],
    queryFn: getCourses,
  });
};
