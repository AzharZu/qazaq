import { Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "./components/ui/toaster";
import AdminLayout from "./components/layout/AdminLayout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import CoursesPage from "./pages/CoursesPage";
import ModulesPage from "./pages/ModulesPage";
import LessonsIndexPage from "./pages/LessonsIndexPage";
import LessonBuilderPage from "./pages/LessonBuilderPage";
import LessonBuilderHierarchyPage from "./pages/LessonBuilderHierarchyPage";
import BlocksPage from "./pages/BlocksPage";
import VocabularyPage from "./pages/VocabularyPage";
import PlacementPage from "./pages/PlacementPage";
import UsersPage from "./pages/UsersPage";
import AutocheckerPage from "./pages/AutocheckerPage";
import RequireAdmin from "./components/auth/RequireAdmin";

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/admin/login" element={<LoginPage />} />
        <Route
          path="/admin"
          element={
            <RequireAdmin>
              <AdminLayout />
            </RequireAdmin>
          }
        >
          <Route index element={<Navigate to="/admin/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="lesson-builder" element={<LessonBuilderHierarchyPage />} />
          <Route path="courses" element={<CoursesPage />} />
          <Route path="courses/:id" element={<CoursesPage />} />
          <Route path="modules/:id" element={<ModulesPage />} />
          <Route path="lessons" element={<LessonsIndexPage />} />
          <Route path="lessons/:lessonId" element={<LessonBuilderPage />} />
          <Route path="lessons/:lessonId/builder" element={<LessonBuilderPage />} />
          <Route path="blocks/:id" element={<BlocksPage />} />
          <Route path="vocabulary" element={<VocabularyPage />} />
          <Route path="placement" element={<PlacementPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="autochecker" element={<AutocheckerPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/admin/login" replace />} />
      </Routes>
      <Toaster />
    </>
  );
}
