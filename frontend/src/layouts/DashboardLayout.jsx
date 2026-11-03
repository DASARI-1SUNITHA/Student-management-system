import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const MENUS = {
  admin: [["", "Dashboard"], ["students", "Students"], ["faculty", "Faculty"], ["departments", "Departments"],
    ["courses", "Courses"], ["subjects", "Subjects"], ["enrollments", "Enrollments"], ["reports", "Reports"], ["change-password", "Change Password"]],
  faculty: [["", "Dashboard"], ["students", "My Students"], ["attendance", "Attendance"], ["marks", "Marks & Grades"], ["change-password", "Change Password"]],
  student: [["", "Dashboard"], ["profile", "My Profile"], ["attendance", "My Attendance"], ["marks", "My Marks"], ["courses", "My Courses"], ["change-password", "Change Password"]],
};

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const base = `/${user.role}`;

  return (
    <div className="shell">
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="brand">🎓 SMS<small>{user.role}</small></div>
        <nav>
          {MENUS[user.role].map(([path, label]) => (
            <NavLink key={label} to={path ? `${base}/${path}` : base} end={!path} onClick={() => setOpen(false)}>{label}</NavLink>
          ))}
        </nav>
      </aside>
      {open && <div className="backdrop" onClick={() => setOpen(false)} />}
      <div className="main">
        <header className="topbar">
          <button className="btn ghost menu-btn" onClick={() => setOpen(!open)}>☰</button>
          <div className="spacer" />
          <div className="who"><strong>{user.name}</strong><span>{user.code ? `${user.code} · ` : ""}{user.email}</span></div>
          <button className="btn" onClick={() => { logout(); nav("/login"); }}>Logout</button>
        </header>
        <main className="content"><Outlet /></main>
      </div>
    </div>
  );
}
