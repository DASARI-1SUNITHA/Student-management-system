import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const homeFor = (role) => `/${role}`;

// UI-level guard only. The REAL enforcement is always done by the backend.
export default function ProtectedRoute({ role }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="center-screen">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={homeFor(user.role)} replace />;
  return <Outlet />;
}
