import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute, { homeFor } from "./routes/ProtectedRoute";
import DashboardLayout from "./layouts/DashboardLayout";
import { useAuth } from "./context/AuthContext";

import Login from "./pages/auth/Login";
import ChangePassword from "./pages/auth/ChangePassword";
import AdminDashboard from "./pages/admin/AdminDashboard";
import Students from "./pages/admin/Students";
import FacultyManagement from "./pages/admin/FacultyManagement";
import { Departments, Courses, Subjects } from "./pages/admin/Academics";
import Enrollments from "./pages/admin/Enrollments";
import Reports from "./pages/admin/Reports";
import FacultyDashboard from "./pages/faculty/FacultyDashboard";
import FacultyStudents from "./pages/faculty/FacultyStudents";
import Attendance from "./pages/faculty/Attendance";
import Marks from "./pages/faculty/Marks";
import StudentDashboard from "./pages/student/StudentDashboard";
import StudentProfile from "./pages/student/StudentProfile";
import StudentAttendance from "./pages/student/StudentAttendance";
import StudentMarks from "./pages/student/StudentMarks";
import StudentCourses from "./pages/student/StudentCourses";

export default function App() {
  const { user, loading } = useAuth();
  if (loading) return <div className="center-screen">Loading…</div>;
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to={homeFor(user.role)} replace /> : <Login />} />

      <Route path="/admin" element={<ProtectedRoute role="admin" />}>
        <Route element={<DashboardLayout />}>
          <Route index element={<AdminDashboard />} />
          <Route path="students" element={<Students />} />
          <Route path="faculty" element={<FacultyManagement />} />
          <Route path="departments" element={<Departments />} />
          <Route path="courses" element={<Courses />} />
          <Route path="subjects" element={<Subjects />} />
          <Route path="enrollments" element={<Enrollments />} />
          <Route path="reports" element={<Reports />} />
          <Route path="change-password" element={<ChangePassword />} />
        </Route>
      </Route>

      <Route path="/faculty" element={<ProtectedRoute role="faculty" />}>
        <Route element={<DashboardLayout />}>
          <Route index element={<FacultyDashboard />} />
          <Route path="students" element={<FacultyStudents />} />
          <Route path="attendance" element={<Attendance />} />
          <Route path="marks" element={<Marks />} />
          <Route path="change-password" element={<ChangePassword />} />
        </Route>
      </Route>

      <Route path="/student" element={<ProtectedRoute role="student" />}>
        <Route element={<DashboardLayout />}>
          <Route index element={<StudentDashboard />} />
          <Route path="profile" element={<StudentProfile />} />
          <Route path="attendance" element={<StudentAttendance />} />
          <Route path="marks" element={<StudentMarks />} />
          <Route path="courses" element={<StudentCourses />} />
          <Route path="change-password" element={<ChangePassword />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to={user ? homeFor(user.role) : "/login"} replace />} />
    </Routes>
  );
}
