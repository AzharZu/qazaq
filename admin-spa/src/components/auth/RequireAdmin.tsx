import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../state/AuthContext";

export default function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="py-12 text-center text-gray-500">Loading...</div>;
  }
  if (!user) {
    return <Navigate to="/admin/login" replace state={{ from: location }} />;
  }
  if (!user.is_admin && (user.role || "").toLowerCase() !== "admin") {
    return <div className="py-12 text-center text-red-600">Admin access required</div>;
  }
  return <>{children}</>;
}
