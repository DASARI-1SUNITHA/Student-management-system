import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errMsg } from "../../services/api";
import useFetch from "../../hooks/useFetch";
import { Loading, PageHeader, useToast } from "../../components/common/ui";

export default function StudentProfile() {
  const notify = useToast();
  const { data: p, loading, error, setData } = useFetch("/student/profile");
  const [f, setF] = useState({ phone: "", address: "" });
  useEffect(() => { if (p) setF({ phone: p.phone || "", address: p.address || "" }); }, [p]);
  if (loading || error) return <Loading error={error} />;

  const save = async (e) => {
    e.preventDefault();
    try {
      const r = await api.put("/student/profile", { phone: f.phone || null, address: f.address || null });
      setData(r.data); notify("Contact details updated");
    } catch (err) { notify(errMsg(err), "error"); }
  };

  return (
    <>
      <PageHeader title="My Profile"><Link className="btn" to="/student/change-password">Change password</Link></PageHeader>
      <div className="grid-2">
        <section className="card"><h3>Personal details</h3>
          <dl className="details">{Object.entries({ "Student ID": p.student_code, Name: p.full_name, Email: p.email, Gender: p.gender, "Date of birth": p.date_of_birth,
            Department: p.department, Course: p.course, "Admission date": p.admission_date, Status: p.status }).map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v || "—"}</dd></div>)}</dl>
          <p className="muted small">These details can only be changed by the administrator.</p>
        </section>
        <form className="card form-grid" onSubmit={save}>
          <h3 className="full">Contact information</h3>
          <label className="full"><span>Phone</span><input value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} placeholder="digits only" /></label>
          <label className="full"><span>Address</span><textarea rows={3} value={f.address} onChange={(e) => setF({ ...f, address: e.target.value })} /></label>
          <div className="full"><button className="btn primary">Save changes</button></div>
        </form>
      </div>
    </>
  );
}
