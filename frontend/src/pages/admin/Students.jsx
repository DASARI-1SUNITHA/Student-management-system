import { useEffect, useState } from "react";
import api, { errMsg } from "../../services/api";
import useFetch from "../../hooks/useFetch";
import { Badge, DataTable, FormModal, Modal, PageHeader, Pagination, useToast } from "../../components/common/ui";

const PAGE_SIZE = 10;

export default function Students() {
  const notify = useToast();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");
  const [dept, setDept] = useState("");
  const [course, setCourse] = useState("");
  const [modal, setModal] = useState(null);
  const [view, setView] = useState(null);

  const { data: depts } = useFetch("/departments");
  const { data: courses } = useFetch("/courses");
  const { data, reload } = useFetch("/admin/students", {
    page, page_size: PAGE_SIZE, search: search || undefined, department_id: dept || undefined, course_id: course || undefined,
  });
  useEffect(() => { setPage(1); }, [search, dept, course]);

  const fields = [
    { name: "student_code", label: "Student ID", required: true },
    { name: "full_name", label: "Full name", required: true },
    { name: "email", label: "Email", type: "email", required: true },
    { name: "password", label: "Initial password (min 8)", type: "password", required: true, createOnly: true, minLength: 8 },
    { name: "phone", label: "Phone (digits only)" },
    { name: "gender", label: "Gender", type: "select", options: [["male", "Male"], ["female", "Female"], ["other", "Other"]] },
    { name: "date_of_birth", label: "Date of birth", type: "date" },
    { name: "admission_date", label: "Admission date", type: "date" },
    { name: "department_id", label: "Department", type: "select", number: true, required: true, resets: ["course_id"], options: (depts || []).map((d) => [d.id, d.name]) },
    { name: "course_id", label: "Course", type: "select", number: true, required: true,
      options: (v) => (courses || []).filter((c) => String(c.department_id) === String(v.department_id)).map((c) => [c.id, c.name]) },
    { name: "status", label: "Status", type: "select", required: true, options: [["active", "Active"], ["inactive", "Inactive"], ["graduated", "Graduated"], ["suspended", "Suspended"]] },
    { name: "address", label: "Address", type: "textarea" },
  ];

  const save = async (vals) => {
    try {
      if (modal.id) await api.put(`/admin/students/${modal.id}`, vals); else await api.post("/admin/students", vals);
      notify(modal.id ? "Student updated" : "Student created with login account");
      setModal(null); reload();
    } catch (e) { notify(errMsg(e), "error"); }
  };
  const toggle = async (s) => {
    try { await api.put(`/admin/students/${s.id}`, { is_active: !s.is_active }); notify(s.is_active ? "Account deactivated" : "Account activated"); reload(); }
    catch (e) { notify(errMsg(e), "error"); }
  };
  const remove = async (s) => {
    if (!window.confirm(`Delete ${s.full_name}? Their attendance and marks will also be deleted.`)) return;
    try { await api.delete(`/admin/students/${s.id}`); notify("Student deleted"); reload(); } catch (e) { notify(errMsg(e), "error"); }
  };

  return (
    <>
      <PageHeader title="Students"><button className="btn primary" onClick={() => setModal({ status: "active" })}>+ Add student</button></PageHeader>
      <form className="filters" onSubmit={(e) => { e.preventDefault(); setSearch(q); }}>
        <input placeholder="Search name, ID or email" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={dept} onChange={(e) => { setDept(e.target.value); setCourse(""); }}>
          <option value="">All departments</option>{(depts || []).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <select value={course} onChange={(e) => setCourse(e.target.value)}>
          <option value="">All courses</option>{(courses || []).filter((c) => !dept || String(c.department_id) === dept).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <button className="btn">Search</button>
      </form>
      <DataTable rows={data?.items} columns={[
        { label: "ID", key: "student_code" }, { label: "Name", key: "full_name" }, { label: "Email", key: "email" },
        { label: "Department", key: "department" }, { label: "Course", key: "course" },
        { label: "Account", render: (s) => <Badge tone={s.is_active ? "green" : "red"}>{s.is_active ? "Active" : "Disabled"}</Badge> },
        { label: "Actions", render: (s) => (
          <div className="row-actions">
            <button className="btn sm" onClick={() => setView(s)}>View</button>
            <button className="btn sm" onClick={() => setModal(s)}>Edit</button>
            <button className="btn sm" onClick={() => toggle(s)}>{s.is_active ? "Deactivate" : "Activate"}</button>
            <button className="btn sm danger" onClick={() => remove(s)}>Delete</button>
          </div>) },
      ]} />
      <Pagination page={page} pageSize={PAGE_SIZE} total={data?.total || 0} onChange={setPage} />
      {modal && <FormModal title={modal.id ? "Edit student" : "Add student"} fields={fields} initial={modal} onSubmit={save} onClose={() => setModal(null)} />}
      {view && (
        <Modal title="Student details" onClose={() => setView(null)}>
          <dl className="details">{Object.entries({ "Student ID": view.student_code, Name: view.full_name, Email: view.email, Phone: view.phone, Gender: view.gender,
            "Date of birth": view.date_of_birth, Address: view.address, Department: view.department, Course: view.course, "Admission date": view.admission_date, Status: view.status })
            .map(([k, val]) => <div key={k}><dt>{k}</dt><dd>{val || "—"}</dd></div>)}</dl>
        </Modal>
      )}
    </>
  );
}
