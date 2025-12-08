import { Navigate, Route, Routes } from "react-router-dom";
import LessonsList from "./pages/LessonsList.jsx";
import LessonEditor from "./pages/LessonEditor.jsx";

function App() {
  return (
    <div className="app-shell">
      <Routes>
        <Route path="/lessons" element={<LessonsList />} />
        <Route path="/lessons/:lessonId/editor" element={<LessonEditor />} />
        <Route path="*" element={<Navigate to="/lessons" replace />} />
      </Routes>
    </div>
  );
}

export default App;
