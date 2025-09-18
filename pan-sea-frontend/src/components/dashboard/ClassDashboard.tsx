// components/ClassDashboard.tsx
"use client";

import { useMemo, useState, useEffect } from "react";
import { ClassItem } from "./class/ClassCard";
import DashboardHeader from "./DashboardHeader";
import ClassGrid from "./class/ClassGrid";
import EmptyState from "./class/EmptyState";
import CreateClassModal from "./class/CreateClassModal";
import { toast } from "react-toastify";
import { useAuth } from "@/hooks/useAuth";
import { fetchClasses, fetchStudentClasses, createClass, deleteClass, CreateClassRequest } from "@/services/classes";
import { filterClasses } from "../../lib/classData";

const CLASS_STORAGE_KEY = "rean.classes.v1";

export default function   ClassDashboard() {
  const { user } = useAuth();
  const [classes, setClasses] = useState<ClassItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Load classes from API
  useEffect(() => {
    async function loadClasses() {
      if (!user?.id) {
        console.log('No user ID available for loading classes');
        setIsLoading(false);
        return;
      }

      const role = user?.role?.toLowerCase?.();
      console.log('Loading classes for user:', { id: user.id, role });

      try {
        setError(null);
        const apiClasses = role === 'student'
          ? await fetchStudentClasses()
          : await fetchClasses(user.id);
        console.log('Fetched classes from API:', apiClasses);
        setClasses(apiClasses);
        
        // Also save to localStorage for the detail page
        localStorage.setItem(CLASS_STORAGE_KEY, JSON.stringify(apiClasses));
      } catch (err) {
        console.error('Error loading classes:', err);
        setError('Failed to load classes. Please try again.');
        
        // Try to load from localStorage as fallback
        try {
          const classesRaw = localStorage.getItem(CLASS_STORAGE_KEY);
          if (classesRaw) {
            const storedClasses: ClassItem[] = JSON.parse(classesRaw);
            console.log('Loaded classes from localStorage:', storedClasses);
            setClasses(storedClasses);
          }
        } catch (storageError) {
          console.error('Error loading from localStorage:', storageError);
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadClasses();
  }, [user?.id]);

  // Save classes to localStorage whenever classes change (for create/update operations)
  useEffect(() => {
    if (!isLoading && classes.length > 0) {
      localStorage.setItem(CLASS_STORAGE_KEY, JSON.stringify(classes));
    }
  }, [classes, isLoading]);

  const filteredClasses = useMemo(() => filterClasses(classes, query), [query, classes]);

  const role = user?.role?.toLowerCase?.();
  const canCreate = role !== undefined && role !== 'student';

  const handleCreateClass = async (classData: CreateClassRequest) => {
    if (!canCreate) {
      toast.error("Students cannot create classes");
      return;
    }
    if (!user?.id) {
      toast.error("Please log in to create a class");
      return;
    }

    try {
      // Set the teacher_id to the current user's ID
      const classDataWithTeacher: CreateClassRequest = {
        ...classData,
        teacher_id: user.id
      };

      console.log('Creating class with data:', classDataWithTeacher);
      const newClass = await createClass(classDataWithTeacher);
      console.log('Class created successfully:', newClass);
      
      setClasses((prev) => [newClass, ...prev]);
      
      // Update localStorage
      const updatedClasses = [newClass, ...classes];
      localStorage.setItem(CLASS_STORAGE_KEY, JSON.stringify(updatedClasses));
      
      toast.success("Class created successfully!");
    } catch (error) {
      console.error('Error creating class:', error);
      toast.error("Failed to create class. Please try again.");
    }
  };

  const handleDeleteClass = async (id: string) => {
    try {
      await deleteClass(id);
      setClasses((prev) => prev.filter((c) => c.id !== id));
      toast.success("Class deleted");
    } catch (error) {
      console.error('Error deleting class:', error);
      toast.error("Failed to delete class");
    }
  };

  const handleOpenModal = () => {
    if (!canCreate) return;
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handleRetry = () => {
    window.location.reload();
  };

  if (isLoading) {
    return (
      <section className="mx-auto max-w-7xl px-6 py-10">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600"></div>
          <p className="ml-3 text-slate-600">Loading classes...</p>
        </div>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-7xl px-6 py-10">
      <DashboardHeader
        searchQuery={query}
        onSearchChange={setQuery}
        onCreateClass={handleOpenModal}
        canCreate={canCreate}
      />

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600">{error}</p>
          <button 
            onClick={handleRetry} 
            className="mt-2 text-sm text-red-800 underline hover:no-underline"
          >
            Try again
          </button>
        </div>
      )}

      {filteredClasses.length === 0 && !error ? (
        <EmptyState onCreateClass={handleOpenModal} canCreate={canCreate} />
      ) : (
        <ClassGrid classes={filteredClasses} onDeleteClass={handleDeleteClass} />
      )}

      <CreateClassModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onCreate={handleCreateClass}
      />

      {/* Toasts are handled globally by ToastProvider */}
    </section>
  );
}
