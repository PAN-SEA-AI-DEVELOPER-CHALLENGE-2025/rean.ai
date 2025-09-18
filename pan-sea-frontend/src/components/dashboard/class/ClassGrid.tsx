"use client";

import ClassCard, { ClassItem } from "./ClassCard";

interface ClassGridProps {
  classes: ClassItem[];
  onDeleteClass: (id: string) => Promise<void> | void;
}

export default function ClassGrid({ classes, onDeleteClass }: ClassGridProps) {
  return (
    <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {classes.map((classItem) => (
        <ClassCard
          key={classItem.id}
          classItem={classItem}
          onDelete={onDeleteClass}
        />
      ))}
    </div>
  );
}
