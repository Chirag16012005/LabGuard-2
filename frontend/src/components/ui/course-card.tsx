import Link from "next/link";
import { Course } from "@/lib/api";

interface CourseCardProps {
  course: Course;
  /** Base path for the link. Defaults to "/dashboard/course" (teacher route). */
  basePath?: string;
}

export function CourseCard({
  course,
  basePath = "/dashboard/course",
}: CourseCardProps) {
  return (
    <Link href={`${basePath}/${course.id}`}>
      <div className="border border-slate-200 rounded-xl p-5 hover:translate-y-[-1px] transition-all duration-200 bg-white hover:border-slate-300 flex flex-col gap-3 group dark:bg-slate-900 dark:border-slate-800 dark:hover:border-slate-700">
        <h3 className="font-semibold text-lg text-slate-800 group-hover:text-blue-600 transition-colors dark:text-slate-100 dark:group-hover:text-blue-400">
          {course.title}
        </h3>
        <p className="text-sm text-slate-500 font-medium dark:text-slate-400">
          {course.subtitle}
        </p>
      </div>
    </Link>
  );
}
