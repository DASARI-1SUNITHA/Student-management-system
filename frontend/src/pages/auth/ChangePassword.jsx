import { useState } from "react";
import api, { errMsg } from "../../services/api";
import { PageHeader, useToast } from "../../components/common/ui";

export default function ChangePassword() {
  const notify = useToast();
  const [f, setF] = useState({ current_password: "", new_password: "", confirm: "" });

  const submit = async (e) => {
    e.preventDefault();
    if (f.new_password !== f.confirm) return notify("New passwords do not match", "error");
    try {
      await api.post("/auth/change-password", { current_password: f.current_password, new_password: f.new_password });
      notify("Password changed");
      setF({ current_password: "", new_password: "", confirm: "" });
    } catch (err) { notify(errMsg(err), "error"); }
  };
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  return (
    <>
      <PageHeader title="Change Password" />
      <form className="card form-grid narrow" onSubmit={submit}>
        <label className="full"><span>Current password</span><input type="password" required value={f.current_password} onChange={set("current_password")} /></label>
        <label className="full"><span>New password (min 8 characters)</span><input type="password" required minLength={8} value={f.new_password} onChange={set("new_password")} /></label>
        <label className="full"><span>Confirm new password</span><input type="password" required minLength={8} value={f.confirm} onChange={set("confirm")} /></label>
        <div className="full"><button className="btn primary">Update password</button></div>
      </form>
    </>
  );
}
