import { useRouter } from "next/navigation";
import { Course } from "@/lib/api";

interface CourseCardProps {
  course: Course;
}

export const CourseCard = ({ course }: CourseCardProps) => {
  const router = useRouter();

  const handleClick = () => {
    router.push(`/dashboard/course/${course.id}`);
  };

  return (
    <div
      onClick={handleClick}
      className="bg-white border border-slate-200 rounded-xl p-5 cursor-pointer transition-all duration-300 hover:-translate-y-[2px] hover:border-sky-400 hover:shadow-sm dark:bg-slate-900/50 dark:border-slate-800 dark:hover:border-sky-500 dark:hover:shadow-none"
    >
      <h3 className="text-lg font-bold mb-1 text-slate-800 dark:text-slate-100">{course.title}</h3>
      <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">{course.teacher}</p>
      
      <div className="flex items-center text-sm font-medium">
        <span className="bg-sky-50 text-sky-700 border border-sky-100 dark:bg-sky-900/30 dark:text-sky-300 dark:border-sky-800/50 px-2.5 py-1 rounded-md">
          {course.assignmentsCount} Assignment{course.assignmentsCount !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  );
};
