import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../state/AuthContext";
import { Button } from "../ui/button";

const links = [
  { to: "/admin/dashboard", label: "Dashboard" },
  { to: "/admin/courses", label: "Courses" },
  { to: "/admin/lessons", label: "Lessons" },
  { to: "/admin/vocabulary", label: "Vocabulary" },
  { to: "/admin/placement", label: "Placement" },
  { to: "/admin/users", label: "Users" },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-[#f7f7fb] text-gray-900">
      <div className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div
              className="h-10 w-10 rounded-lg bg-blue-600 text-white font-bold grid place-items-center cursor-pointer"
              onClick={() => navigate("/admin/dashboard")}
            >
              QA
            </div>
            <div className="flex gap-3 text-sm">
              {links.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) =>
                    `rounded-md px-3 py-2 font-medium ${
                      isActive ? "bg-blue-50 text-blue-700" : "text-gray-700 hover:bg-gray-100"
                    }`
                  }
                >
                  {link.label}
                </NavLink>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <div className="text-right">
              <div className="font-semibold">{user?.email}</div>
              <div className="text-gray-500">{user?.role || "admin"}</div>
            </div>
            <Button variant="outline" onClick={logout}>
              Logout
            </Button>
          </div>
        </div>
      </div>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
