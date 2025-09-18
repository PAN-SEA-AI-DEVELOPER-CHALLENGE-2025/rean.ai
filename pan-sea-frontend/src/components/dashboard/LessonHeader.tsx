import Link from "next/link";
import { FaArrowLeft } from "react-icons/fa";

type LessonHeaderProps = {
  classId: string;
  lessonTitle: string;
  lessonDateTime: string;
};

export default function LessonHeader({ 
  classId, 
  lessonTitle, 
  lessonDateTime 
}: LessonHeaderProps) {
  return (
    <div className="bg-white border-b border-slate-200 px-6 py-4">
      <div className="flex items-center space-x-4">
        <Link 
          href={`/dashboard/class_detail/${classId}`}
          className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <FaArrowLeft className="text-slate-600" />
        </Link>
        <div>
          <h1 className="text-lg font-semibold text-slate-900">{lessonTitle}</h1>
          <p className="text-sm text-slate-500">{lessonDateTime}</p>
        </div>
      </div>
    </div>
  );
}
