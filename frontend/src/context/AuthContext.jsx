import { createContext, useContext, useEffect, useState } from "react";
import api from "../services/api";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!sessionStorage.getItem("token"));

  // On page refresh, re-verify the stored token with the backend.
  useEffect(() => {
    if (!sessionStorage.getItem("token")) return;
    api.get("/auth/me")
      .then((r) => setUser(r.data))
      .catch(() => sessionStorage.clear())
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password, role) => {
    const r = await api.post("/auth/login", { email, password, role });
    sessionStorage.setItem("token", r.data.access_token);
    setUser(r.data.user);
    return r.data.user;
  };

  const logout = () => {
    sessionStorage.clear();
    setUser(null);
  };

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}
