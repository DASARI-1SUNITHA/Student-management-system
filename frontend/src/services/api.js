import axios from "axios";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? (import.meta.env.PROD ? "/api" : "http://localhost:8000") });

// Attach the JWT to every request. sessionStorage is cleared when the tab closes.
api.interceptors.request.use((cfg) => {
  const token = sessionStorage.getItem("token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

// Expired / invalid token -> clear session and go to login.
api.interceptors.response.use(
  (r) => r,
  (err) => {
    const isLogin = err.config?.url?.includes("/auth/login");
    if (err.response?.status === 401 && !isLogin) {
      sessionStorage.clear();
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export function errMsg(e) {
  const d = e.response?.data?.detail;
  if (Array.isArray(d)) return d.map((x) => `${x.loc.slice(1).join(".")}: ${x.msg}`).join("; ");
  return d || e.message || "Something went wrong";
}

export async function downloadFile(path, filename) {
  const r = await api.get(path, { responseType: "blob" });
  const url = URL.createObjectURL(r.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default api;
