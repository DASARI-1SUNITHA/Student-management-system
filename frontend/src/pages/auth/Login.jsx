import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { errMsg } from "../../services/api";
import { homeFor } from "../../routes/ProtectedRoute";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [role, setRole] = useState("student");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const u = await login(email.trim(), password, role);
      nav(homeFor(u.role), { replace: true });
    } catch (err) { setError(errMsg(err)); } finally { setBusy(false); }
  };

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={submit}>
        <h1>🎓 Student Management System</h1>
        <p className="muted">Sign in to continue</p>
        <div className="tabs">
          {["student", "faculty", "admin"].map((r) => (
            <button type="button" key={r} className={role === r ? "active" : ""} onClick={() => setRole(r)}>{r}</button>
          ))}
        </div>
        {error && <div className="alert">{error}</div>}
        <label><span>Email</span><input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" /></label>
        <label><span>Password</span><input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" /></label>
        <button className="btn primary block" disabled={busy}>{busy ? "Signing in…" : `Sign in as ${role}`}</button>
        <p className="muted small">Accounts are created by the administrator. There is no public registration.</p>
      </form>
    </div>
  );
}
