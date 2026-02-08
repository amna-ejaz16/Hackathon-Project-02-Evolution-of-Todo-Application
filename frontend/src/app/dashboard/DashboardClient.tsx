"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { signOut } from "@/lib/auth-client";
import { api, ApiError } from "@/lib/api";
import ChatWidget from "@/components/chat/ChatWidget";

/**
 * Session user type from Better Auth.
 */
interface SessionUser {
  id: string;
  email: string;
  name?: string | null;
}

/**
 * Props passed from server component.
 */
interface DashboardClientProps {
  user: SessionUser;
}

/**
 * Task type matching backend API response.
 */
interface Task {
  id: number;
  title: string;
  description: string | null;
  completed: boolean;
  priority: "low" | "medium" | "high";
  category: string | null;
  due_date: string | null; // ISO date format
  created_at: string;
  updated_at: string;
}

/**
 * API response for task list endpoint.
 */
interface TasksResponse {
  tasks: Task[];
  total: number;
}

/**
 * Form data for creating a new task.
 */
interface TaskFormData {
  title: string;
  description: string;
  priority: "low" | "medium" | "high";
  category: string;
  due_date: string;
}

/**
 * Priority badge color mapping for dark theme.
 */
const priorityColors = {
  low: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  medium: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  high: "bg-red-500/20 text-red-400 border-red-500/30",
};

/**
 * Priority display labels.
 */
const priorityLabels = {
  low: "Low",
  medium: "Medium",
  high: "High",
};

/**
 * Feature cards data.
 */
const featureCards = [
  {
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
    title: "Smart Task Management",
    description: "Organize all your tasks in one place with clear priorities and due dates.",
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    title: "Boost Productivity",
    description: "Stay focused and get more done with a clean, distraction-free workflow.",
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
    ),
    title: "Secure & Personal",
    description: "Your tasks are private, secure, and always linked to your account.",
  },
];

/**
 * Dashboard Client Component
 *
 * This is a CLIENT component that receives a VALIDATED session from the server.
 * Authentication is handled by the parent server component (page.tsx).
 *
 * NO CLIENT-SIDE AUTH REDIRECTS - the server component handles all auth validation.
 *
 * Features:
 * - Create new tasks with title, description, priority, category, due date
 * - View task list with all details
 * - Toggle task completion status
 * - Edit existing tasks
 * - Delete tasks with confirmation
 * - Loading states for all operations
 */
export default function DashboardClient({ user }: DashboardClientProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [editingTaskId, setEditingTaskId] = useState<number | null>(null);
  const [showTaskForm, setShowTaskForm] = useState(false);

  // Track if initial load has been attempted
  const hasAttemptedLoad = useRef(false);

  // Filter and sort state
  const [filters, setFilters] = useState({
    search: "",
    completed: null as boolean | null,
    priority: null as "low" | "medium" | "high" | null,
    category: null as string | null,
    sort: "created_at" as "created_at" | "updated_at" | "due_date" | "priority" | "title",
    order: "desc" as "asc" | "desc",
  });

  // Extract unique categories from tasks for filter dropdown
  const availableCategories = Array.from(
    new Set(tasks.map((task) => task.category).filter((cat): cat is string => cat !== null))
  ).sort();

  // Task form state
  const [formData, setFormData] = useState<TaskFormData>({
    title: "",
    description: "",
    priority: "medium",
    category: "",
    due_date: "",
  });

  // Edit form state
  const [editFormData, setEditFormData] = useState<TaskFormData>({
    title: "",
    description: "",
    priority: "medium",
    category: "",
    due_date: "",
  });

  /**
   * Fetch all tasks from API with filters applied.
   */
  const fetchTasks = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Build query parameters from filters
      const params = new URLSearchParams();
      if (filters.completed !== null) {
        params.append("completed", String(filters.completed));
      }
      if (filters.priority !== null) {
        params.append("priority", filters.priority);
      }
      if (filters.category !== null) {
        params.append("category", filters.category);
      }
      params.append("sort", filters.sort);
      params.append("order", filters.order);

      const url = `/api/tasks${params.toString() ? `?${params.toString()}` : ""}`;
      const response = await api.get<TasksResponse>(url);
      setTasks(response.tasks);
      console.log("Dashboard: Tasks loaded successfully:", response.tasks.length);
    } catch (err) {
      if (err instanceof ApiError) {
        console.error("Dashboard: API error:", err.status, err.message);
        // Show error but don't auto-redirect - server handles auth
        setError(err.message);
      } else {
        console.error("Dashboard: Unknown error:", err);
        setError("Failed to load tasks. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Load tasks on mount.
   * Session is already validated by server component, so we can load immediately.
   */
  useEffect(() => {
    if (!hasAttemptedLoad.current) {
      hasAttemptedLoad.current = true;
      console.log("Dashboard: Loading tasks for user:", user.email);
      fetchTasks();
    }
  }, [user.email]);

  /**
   * Refetch tasks when filters change.
   */
  useEffect(() => {
    if (hasAttemptedLoad.current) {
      fetchTasks();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  /**
   * Handle sign out action.
   */
  const handleSignOut = async () => {
    try {
      await signOut();
      // Full page reload to clear all state and let server redirect
      window.location.href = "/signin";
    } catch (err) {
      console.error("Sign out failed:", err);
    }
  };

  /**
   * Handle form input changes.
   */
  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  /**
   * Handle edit form input changes.
   */
  const handleEditInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setEditFormData((prev) => ({ ...prev, [name]: value }));
  };

  /**
   * Create a new task.
   */
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim()) {
      setError("Task title is required.");
      return;
    }

    try {
      setIsCreating(true);
      setError(null);

      const payload: Record<string, unknown> = {
        title: formData.title.trim(),
      };

      if (formData.description.trim()) {
        payload.description = formData.description.trim();
      }
      if (formData.category.trim()) {
        payload.category = formData.category.trim();
      }
      if (formData.due_date) {
        payload.due_date = formData.due_date;
      }
      payload.priority = formData.priority;

      await api.post("/api/tasks", payload);

      setFormData({
        title: "",
        description: "",
        priority: "medium",
        category: "",
        due_date: "",
      });
      setShowTaskForm(false);
      await fetchTasks();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to create task. Please try again.");
      }
    } finally {
      setIsCreating(false);
    }
  };

  /**
   * Toggle task completion status.
   */
  const handleToggleComplete = async (task: Task) => {
    try {
      if (task.completed) {
        await api.delete(`/api/tasks/${task.id}/complete`);
      } else {
        await api.post(`/api/tasks/${task.id}/complete`);
      }
      await fetchTasks();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to update task status. Please try again.");
      }
    }
  };

  /**
   * Start editing a task.
   */
  const handleStartEdit = (task: Task) => {
    setEditingTaskId(task.id);
    setEditFormData({
      title: task.title,
      description: task.description || "",
      priority: task.priority,
      category: task.category || "",
      due_date: task.due_date || "",
    });
    setError(null);
  };

  /**
   * Cancel editing.
   */
  const handleCancelEdit = () => {
    setEditingTaskId(null);
    setEditFormData({
      title: "",
      description: "",
      priority: "medium",
      category: "",
      due_date: "",
    });
    setError(null);
  };

  /**
   * Save task edits.
   */
  const handleSaveEdit = async (taskId: number) => {
    if (!editFormData.title.trim()) {
      setError("Task title is required.");
      return;
    }

    try {
      setError(null);

      const payload: Record<string, unknown> = {
        title: editFormData.title.trim(),
      };

      if (editFormData.description.trim()) {
        payload.description = editFormData.description.trim();
      } else {
        payload.description = null;
      }

      if (editFormData.category.trim()) {
        payload.category = editFormData.category.trim();
      } else {
        payload.category = null;
      }

      if (editFormData.due_date) {
        payload.due_date = editFormData.due_date;
      } else {
        payload.due_date = null;
      }

      payload.priority = editFormData.priority;

      await api.patch(`/api/tasks/${taskId}`, payload);

      setEditingTaskId(null);
      await fetchTasks();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to update task. Please try again.");
      }
    }
  };

  /**
   * Delete a task with confirmation.
   */
  const handleDeleteTask = async (taskId: number, taskTitle: string) => {
    if (!confirm(`Are you sure you want to delete "${taskTitle}"?`)) {
      return;
    }

    try {
      setError(null);
      await api.delete(`/api/tasks/${taskId}`);
      await fetchTasks();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to delete task. Please try again.");
      }
    }
  };

  /**
   * Format date for display.
   */
  const formatDate = (isoDate: string | null): string => {
    if (!isoDate) return "No due date";
    const date = new Date(isoDate);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  /**
   * Handle filter changes.
   */
  const handleFilterChange = (key: keyof typeof filters, value: unknown) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  /**
   * Clear all filters and reset to defaults.
   */
  const handleClearFilters = () => {
    setFilters({
      search: "",
      completed: null,
      priority: null,
      category: null,
      sort: "created_at",
      order: "desc",
    });
  };

  /**
   * Client-side filter for search (title and description).
   */
  const filteredTasks = tasks.filter((task) => {
    if (!filters.search.trim()) return true;
    const searchLower = filters.search.toLowerCase();
    return (
      task.title.toLowerCase().includes(searchLower) ||
      (task.description && task.description.toLowerCase().includes(searchLower))
    );
  });

  /**
   * Check if any filters are active.
   */
  const hasActiveFilters =
    filters.search !== "" ||
    filters.completed !== null ||
    filters.priority !== null ||
    filters.category !== null ||
    filters.sort !== "created_at" ||
    filters.order !== "desc";

  return (
    <div className="min-h-screen bg-dark-950 relative overflow-hidden">
      {/* Background gradient effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-neon-purple/10 rounded-full blur-[150px]" />
        <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-neon-magenta/10 rounded-full blur-[150px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-neon-violet/5 rounded-full blur-[200px]" />
      </div>

      {/* Navbar */}
      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="sticky top-0 z-50 glass-strong border-b border-dark-600"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            {/* Logo + App Name */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neon-purple to-neon-magenta flex items-center justify-center shadow-neon-sm">
                <svg
                  className="w-6 h-6 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={3}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <span className="text-xl font-bold text-gradient">Task Manager</span>
            </div>

            {/* User Info + Sign Out */}
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-400 hidden sm:block">{user.email}</span>
              <button
                onClick={handleSignOut}
                className="btn-neon px-4 py-2 text-sm"
                aria-label="Sign out"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </motion.nav>

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-center py-12 mb-12"
        >
          <motion.h1
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-4xl md:text-5xl font-bold text-white mb-4"
          >
            Organize your chaos.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="text-xl text-gradient font-medium"
          >
            One task at a time.
          </motion.p>
        </motion.section>

        {/* Feature Cards */}
        <motion.section
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12"
        >
          {featureCards.map((card, index) => (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.5 + index * 0.1 }}
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
              className="feature-card p-6"
            >
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-neon-purple/20 to-neon-magenta/20 flex items-center justify-center mb-4 text-neon-purple">
                {card.icon}
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{card.title}</h3>
              <p className="text-gray-400 text-sm">{card.description}</p>
            </motion.div>
          ))}
        </motion.section>

        {/* Error Alert */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl"
              role="alert"
            >
              <div className="flex justify-between items-start gap-4">
                <div className="flex-grow">
                  <p className="text-red-400 font-medium">{error}</p>
                  <button
                    onClick={() => {
                      setError(null);
                      fetchTasks();
                    }}
                    className="mt-2 text-sm text-red-400/80 underline hover:text-red-300"
                  >
                    Retry loading tasks
                  </button>
                </div>
                <button
                  onClick={() => setError(null)}
                  className="text-red-400 hover:text-red-300 font-bold text-xl leading-none"
                  aria-label="Dismiss error"
                >
                  ×
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Create Task Toggle Button */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mb-6"
        >
          <button
            onClick={() => setShowTaskForm(!showTaskForm)}
            className="btn-neon flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {showTaskForm ? "Hide Form" : "Create New Task"}
          </button>
        </motion.div>

        {/* Create Task Form */}
        <AnimatePresence>
          {showTaskForm && (
            <motion.section
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="card-glow p-6 mb-8 overflow-hidden"
            >
              <h2 className="text-xl font-semibold text-white mb-4">Create New Task</h2>
              <form onSubmit={handleCreateTask} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Title */}
                  <div className="md:col-span-2">
                    <label htmlFor="title" className="block text-sm font-medium text-gray-300 mb-2">
                      Title <span className="text-neon-magenta">*</span>
                    </label>
                    <input
                      type="text"
                      id="title"
                      name="title"
                      value={formData.title}
                      onChange={handleInputChange}
                      required
                      className="input-dark"
                      placeholder="Enter task title"
                      aria-required="true"
                    />
                  </div>

                  {/* Description */}
                  <div className="md:col-span-2">
                    <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-2">
                      Description
                    </label>
                    <textarea
                      id="description"
                      name="description"
                      value={formData.description}
                      onChange={handleInputChange}
                      rows={3}
                      className="input-dark resize-none"
                      placeholder="Add task details (optional)"
                    />
                  </div>

                  {/* Priority */}
                  <div>
                    <label htmlFor="priority" className="block text-sm font-medium text-gray-300 mb-2">
                      Priority
                    </label>
                    <select
                      id="priority"
                      name="priority"
                      value={formData.priority}
                      onChange={handleInputChange}
                      className="input-dark"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>

                  {/* Category */}
                  <div>
                    <label htmlFor="category" className="block text-sm font-medium text-gray-300 mb-2">
                      Category
                    </label>
                    <input
                      type="text"
                      id="category"
                      name="category"
                      value={formData.category}
                      onChange={handleInputChange}
                      className="input-dark"
                      placeholder="e.g., Work, Personal, Shopping"
                    />
                  </div>

                  {/* Due Date */}
                  <div className="md:col-span-2">
                    <label htmlFor="due_date" className="block text-sm font-medium text-gray-300 mb-2">
                      Due Date
                    </label>
                    <input
                      type="date"
                      id="due_date"
                      name="due_date"
                      value={formData.due_date}
                      onChange={handleInputChange}
                      className="input-dark"
                    />
                  </div>
                </div>

                {/* Submit Button */}
                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={isCreating}
                    className="btn-neon"
                    aria-label="Create task"
                  >
                    {isCreating ? (
                      <span className="flex items-center gap-2">
                        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Creating...
                      </span>
                    ) : (
                      "Create Task"
                    )}
                  </button>
                </div>
              </form>
            </motion.section>
          )}
        </AnimatePresence>

        {/* Filter and Search Panel */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="card-dark p-6 mb-8"
        >
          <div className="flex flex-col lg:flex-row lg:items-end gap-4">
            {/* Search Input */}
            <div className="flex-grow">
              <label htmlFor="search" className="block text-sm font-medium text-gray-300 mb-2">
                Search
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <svg
                    className="h-5 w-5 text-gray-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </div>
                <input
                  type="text"
                  id="search"
                  value={filters.search}
                  onChange={(e) => handleFilterChange("search", e.target.value)}
                  className="input-dark pl-12"
                  placeholder="Search tasks by title or description..."
                  aria-label="Search tasks"
                />
              </div>
            </div>

            {/* Status Filter */}
            <div className="w-full lg:w-48">
              <label htmlFor="status-filter" className="block text-sm font-medium text-gray-300 mb-2">
                Status
              </label>
              <select
                id="status-filter"
                value={filters.completed === null ? "all" : filters.completed ? "completed" : "active"}
                onChange={(e) =>
                  handleFilterChange(
                    "completed",
                    e.target.value === "all" ? null : e.target.value === "completed"
                  )
                }
                className="input-dark"
                aria-label="Filter by status"
              >
                <option value="all">All Tasks</option>
                <option value="active">Active</option>
                <option value="completed">Completed</option>
              </select>
            </div>

            {/* Priority Filter */}
            <div className="w-full lg:w-48">
              <label htmlFor="priority-filter" className="block text-sm font-medium text-gray-300 mb-2">
                Priority
              </label>
              <select
                id="priority-filter"
                value={filters.priority || "all"}
                onChange={(e) =>
                  handleFilterChange("priority", e.target.value === "all" ? null : e.target.value)
                }
                className="input-dark"
                aria-label="Filter by priority"
              >
                <option value="all">All Priorities</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            {/* Category Filter */}
            <div className="w-full lg:w-48">
              <label htmlFor="category-filter" className="block text-sm font-medium text-gray-300 mb-2">
                Category
              </label>
              <select
                id="category-filter"
                value={filters.category || "all"}
                onChange={(e) =>
                  handleFilterChange("category", e.target.value === "all" ? null : e.target.value)
                }
                className="input-dark"
                aria-label="Filter by category"
              >
                <option value="all">All Categories</option>
                {availableCategories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Sort Controls */}
          <div className="flex flex-col sm:flex-row gap-4 mt-4 pt-4 border-t border-dark-600">
            <div className="flex-grow sm:flex-grow-0">
              <label htmlFor="sort-field" className="block text-sm font-medium text-gray-300 mb-2">
                Sort By
              </label>
              <select
                id="sort-field"
                value={filters.sort}
                onChange={(e) => handleFilterChange("sort", e.target.value)}
                className="input-dark w-full sm:w-48"
                aria-label="Sort field"
              >
                <option value="created_at">Created Date</option>
                <option value="updated_at">Updated Date</option>
                <option value="due_date">Due Date</option>
                <option value="priority">Priority</option>
                <option value="title">Title</option>
              </select>
            </div>

            <div className="flex-grow sm:flex-grow-0">
              <label htmlFor="sort-order" className="block text-sm font-medium text-gray-300 mb-2">
                Order
              </label>
              <select
                id="sort-order"
                value={filters.order}
                onChange={(e) => handleFilterChange("order", e.target.value as "asc" | "desc")}
                className="input-dark w-full sm:w-48"
                aria-label="Sort order"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>

            {/* Clear Filters Button */}
            <div className="flex items-end">
              <button
                onClick={handleClearFilters}
                disabled={!hasActiveFilters}
                className={`px-4 py-3 text-sm font-medium rounded-xl border transition-all duration-300 ${
                  hasActiveFilters
                    ? "bg-dark-700 text-gray-300 border-dark-500 hover:border-neon-purple/50 hover:text-white"
                    : "bg-dark-800 text-gray-600 border-dark-700 cursor-not-allowed"
                }`}
                aria-label="Clear all filters"
              >
                Clear Filters
              </button>
            </div>
          </div>

          {/* Active Filters Indicator */}
          <AnimatePresence>
            {hasActiveFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4 pt-4 border-t border-dark-600"
              >
                <div className="flex flex-wrap gap-2 items-center">
                  <span className="text-sm font-medium text-gray-400">Active filters:</span>
                  {filters.search && (
                    <span className="px-3 py-1 bg-neon-purple/10 text-neon-purple text-xs rounded-full border border-neon-purple/30">
                      Search: &quot;{filters.search}&quot;
                    </span>
                  )}
                  {filters.completed !== null && (
                    <span className="px-3 py-1 bg-neon-purple/10 text-neon-purple text-xs rounded-full border border-neon-purple/30">
                      {filters.completed ? "Completed" : "Active"} tasks
                    </span>
                  )}
                  {filters.priority && (
                    <span className="px-3 py-1 bg-neon-purple/10 text-neon-purple text-xs rounded-full border border-neon-purple/30">
                      {priorityLabels[filters.priority]} priority
                    </span>
                  )}
                  {filters.category && (
                    <span className="px-3 py-1 bg-neon-purple/10 text-neon-purple text-xs rounded-full border border-neon-purple/30">
                      Category: {filters.category}
                    </span>
                  )}
                  {(filters.sort !== "created_at" || filters.order !== "desc") && (
                    <span className="px-3 py-1 bg-neon-purple/10 text-neon-purple text-xs rounded-full border border-neon-purple/30">
                      Sort: {filters.sort} ({filters.order})
                    </span>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.section>

        {/* Task List */}
        <motion.section
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
        >
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold text-white">
              My Tasks {!isLoading && <span className="text-gray-500">({filteredTasks.length})</span>}
            </h2>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="card-dark p-12 text-center">
              <div className="relative w-16 h-16 mx-auto mb-4">
                <div className="absolute inset-0 rounded-full border-4 border-dark-600"></div>
                <div className="absolute inset-0 rounded-full border-4 border-neon-purple border-t-transparent animate-spin"></div>
              </div>
              <p className="text-gray-400">Loading tasks...</p>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && tasks.length === 0 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="card-dark p-12 text-center"
            >
              <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-neon-purple/20 to-neon-magenta/20 flex items-center justify-center">
                <svg
                  className="w-10 h-10 text-neon-purple"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-white mb-2">No tasks yet</h3>
              <p className="text-gray-400 mb-4">Get started by creating a new task above.</p>
              <button
                onClick={() => setShowTaskForm(true)}
                className="btn-neon"
              >
                Create Your First Task
              </button>
            </motion.div>
          )}

          {/* No Results State */}
          {!isLoading && tasks.length > 0 && filteredTasks.length === 0 && (
            <div className="card-dark p-12 text-center">
              <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center">
                <svg
                  className="w-10 h-10 text-amber-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-white mb-2">No matching tasks</h3>
              <p className="text-gray-400 mb-4">
                Try adjusting your filters or search terms to find what you&apos;re looking for.
              </p>
              <button
                onClick={handleClearFilters}
                className="text-neon-purple hover:text-neon-pink underline transition-colors"
              >
                Clear all filters
              </button>
            </div>
          )}

          {/* Task Cards */}
          {!isLoading && filteredTasks.length > 0 && (
            <div className="space-y-4">
              <AnimatePresence>
                {filteredTasks.map((task, index) => (
                  <motion.div
                    key={task.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                    className={`card-dark p-6 transition-all duration-300 ${
                      task.completed ? "opacity-60" : ""
                    } hover:border-neon-purple/30`}
                  >
                    {editingTaskId === task.id ? (
                      /* Edit Mode */
                      <div className="space-y-4">
                        <div>
                          <label htmlFor={`edit-title-${task.id}`} className="block text-sm font-medium text-gray-300 mb-2">
                            Title <span className="text-neon-magenta">*</span>
                          </label>
                          <input
                            type="text"
                            id={`edit-title-${task.id}`}
                            name="title"
                            value={editFormData.title}
                            onChange={handleEditInputChange}
                            required
                            className="input-dark"
                          />
                        </div>

                        <div>
                          <label htmlFor={`edit-description-${task.id}`} className="block text-sm font-medium text-gray-300 mb-2">
                            Description
                          </label>
                          <textarea
                            id={`edit-description-${task.id}`}
                            name="description"
                            value={editFormData.description}
                            onChange={handleEditInputChange}
                            rows={3}
                            className="input-dark resize-none"
                          />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <label htmlFor={`edit-priority-${task.id}`} className="block text-sm font-medium text-gray-300 mb-2">
                              Priority
                            </label>
                            <select
                              id={`edit-priority-${task.id}`}
                              name="priority"
                              value={editFormData.priority}
                              onChange={handleEditInputChange}
                              className="input-dark"
                            >
                              <option value="low">Low</option>
                              <option value="medium">Medium</option>
                              <option value="high">High</option>
                            </select>
                          </div>

                          <div>
                            <label htmlFor={`edit-category-${task.id}`} className="block text-sm font-medium text-gray-300 mb-2">
                              Category
                            </label>
                            <input
                              type="text"
                              id={`edit-category-${task.id}`}
                              name="category"
                              value={editFormData.category}
                              onChange={handleEditInputChange}
                              className="input-dark"
                            />
                          </div>

                          <div>
                            <label htmlFor={`edit-due_date-${task.id}`} className="block text-sm font-medium text-gray-300 mb-2">
                              Due Date
                            </label>
                            <input
                              type="date"
                              id={`edit-due_date-${task.id}`}
                              name="due_date"
                              value={editFormData.due_date}
                              onChange={handleEditInputChange}
                              className="input-dark"
                            />
                          </div>
                        </div>

                        <div className="flex justify-end gap-3">
                          <button
                            onClick={handleCancelEdit}
                            className="px-4 py-2 text-sm font-medium text-gray-300 bg-dark-700 rounded-xl border border-dark-500 hover:border-gray-500 transition-colors"
                            aria-label="Cancel editing"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={() => handleSaveEdit(task.id)}
                            className="btn-neon px-4 py-2 text-sm"
                            aria-label="Save changes"
                          >
                            Save Changes
                          </button>
                        </div>
                      </div>
                    ) : (
                      /* View Mode */
                      <>
                        <div className="flex items-start gap-4">
                          {/* Completion Checkbox */}
                          <div className="flex-shrink-0 pt-1">
                            <button
                              onClick={() => handleToggleComplete(task)}
                              className={`w-6 h-6 rounded-lg border-2 flex items-center justify-center transition-all duration-300 ${
                                task.completed
                                  ? "bg-gradient-to-br from-neon-purple to-neon-magenta border-transparent"
                                  : "border-dark-500 hover:border-neon-purple"
                              }`}
                              aria-label={`Mark task "${task.title}" as ${task.completed ? "incomplete" : "complete"}`}
                            >
                              {task.completed && (
                                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                </svg>
                              )}
                            </button>
                          </div>

                          {/* Task Content */}
                          <div className="flex-grow min-w-0">
                            <div className="flex items-start justify-between gap-4 mb-2">
                              <h3
                                className={`text-lg font-semibold ${
                                  task.completed ? "line-through text-gray-500" : "text-white"
                                }`}
                              >
                                {task.title}
                              </h3>

                              {/* Action Buttons */}
                              <div className="flex gap-2 flex-shrink-0">
                                <button
                                  onClick={() => handleStartEdit(task)}
                                  className="p-2 text-neon-purple hover:bg-neon-purple/10 rounded-lg transition-colors"
                                  aria-label={`Edit task "${task.title}"`}
                                  title="Edit task"
                                >
                                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() => handleDeleteTask(task.id, task.title)}
                                  className="p-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                                  aria-label={`Delete task "${task.title}"`}
                                  title="Delete task"
                                >
                                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                  </svg>
                                </button>
                              </div>
                            </div>

                            {/* Description */}
                            {task.description && (
                              <p className={`text-gray-400 mb-3 ${task.completed ? "line-through" : ""}`}>
                                {task.description}
                              </p>
                            )}

                            {/* Metadata */}
                            <div className="flex flex-wrap gap-2 items-center">
                              {/* Priority Badge */}
                              <span
                                className={`px-3 py-1 text-xs font-medium rounded-full border ${
                                  priorityColors[task.priority]
                                }`}
                              >
                                {priorityLabels[task.priority]} Priority
                              </span>

                              {/* Category */}
                              {task.category && (
                                <span className="px-3 py-1 text-xs font-medium bg-neon-purple/10 text-neon-purple rounded-full border border-neon-purple/30">
                                  {task.category}
                                </span>
                              )}

                              {/* Due Date */}
                              <span className="px-3 py-1 text-xs font-medium bg-dark-700 text-gray-400 rounded-full border border-dark-500">
                                Due: {formatDate(task.due_date)}
                              </span>
                            </div>
                          </div>
                        </div>
                      </>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </motion.section>
      </main>

      {/* AI Chat Widget */}
      <ChatWidget onTaskChange={fetchTasks} />
    </div>
  );
}
