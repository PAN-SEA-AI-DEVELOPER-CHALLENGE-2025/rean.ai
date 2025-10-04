// Export all dashboard components from a single index file
export { default as ClassDashboard } from "./ClassDashboard";
export { default as ClassCard } from "./class/ClassCard";
export { default as ClassGrid } from "./class/ClassGrid";
export { default as CreateClassModal } from "./class/CreateClassModal";
export { default as DashboardHeader } from "./DashboardHeader";
export { default as EmptyState } from "./class/EmptyState";
export { default as SearchBar } from "./SearchBar";
export { default as Toast } from "./Toast";

// Re-export types
export type { ClassItem } from "./class/ClassCard";
