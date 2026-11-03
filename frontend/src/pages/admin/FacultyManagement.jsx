import { useEffect, useState } from "react";
import api, { errMsg } from "../../services/api";
import useFetch from "../../hooks/useFetch";
import { Badge, DataTable, FormModal, Modal, PageHeader, Pagination, useToast } from "../../components/common/ui";

const PAGE_SIZE = 10;

export default function FacultyManagement() {
  const notify = useToast();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");
  const [modal, setModal] = useState(null);
  const [assign, setAssign] = useState(null);
  const [picked, setPicked] = useState([]);

  const { data: depts } = useFetch("/departments");
  const { data: courses } = useFetch("/courses");
  const { data, reload } = useFetch("/admin/faculty", { page, page_size: PAGE_SIZE, search: search || undefined });
  useEffect(() => { setPage(1); }, [search]);

  const fields = [
    { name: "faculty_code", label: "Faculty ID", required: true },
    { name: "full_name", label: "Full name", required: true },
    { name: "email", label: "Email", type: "email", required: true },
    { name: "password", label: "Initial password (min 8)", type: "password", required: true, createOnly: true, minLength: 8 },
    { name: "phone", label: "Phone (digits only)" },
    { name: "department_id", label: "Department", type: "select", number: true, required: true, options: (depts || []).map((d) => [d.id, d.name]) },
    { name: "qualification", label: "Qualification" },
    { name: "designation", label: "Designation" },
  ];

  const save = async (vals) => {
    try {
      if (modal.id) await api.put(`/admin/faculty/${modal.id}`, vals); else await api.post("/admin/faculty", vals);
      notify(modal.id ? "Faculty updated" : "Faculty created with login account"); setModal(null); reload();
    } catch (e) { notify(errMsg(e), "error"); }
  };
  const toggle = async (f) => {
    try { await api.put(`/admin/faculty/${f.id}`, { is_active: !f.is_active }); reload(); } catch (e) { notify(errMsg(e), "error"); }
  };
  const remove = async (f) => {
    if (!window.confirm(`Delete ${f.full_name}? Consider deactivating instead.`)) return;
    try { await api.delete(`/admin/faculty/${f.id}`); notify("Faculty deleted"); reload(); } catch (e) { notify(errMsg(e), "error"); }
  };
  const saveAssign = async () => {
    try { await api.post(`/admin/faculty/${assign.id}/courses`, { course_ids: picked }); notify("Courses assigned"); setAssign(null); reload(); }
    catch (e) { notify(errMsg(e), "error"); }
  };

  return (
    <>
      <PageHeader title="Faculty"><button className="btn primary" onClick={() => setModal({})}>+ Add faculty</button></PageHeader>
      <form className="filters" onSubmit={(e) => { e.preventDefault(); setSearch(q); }}>
        <input placeholder="Search name, ID or email" value={q} onChange={(e) => setQ(e.target.value)} /><button className="btn">Search</button>
      </form>
      <DataTable rows={data?.items} columns={[
        { label: "ID", key: "faculty_code" }, { label: "Name", key: "full_name" }, { label: "Email", key: "email" },
        { label: "Department", key: "department" }, { label: "Designation", key: "designation" },
        { label: "Courses", render: (f) => f.courses.join(", ") || "—" },
        { label: "Account", render: (f) => <Badge tone={f.is_active ? "green" : "red"}>{f.is_active ? "Active" : "Disabled"}</Badge> },
        { label: "Actions", render: (f) => (
          <div className="row-actions">
            <button className="btn sm" onClick={() => { setAssign(f); setPicked(f.course_ids); }}>Courses</button>
            <button className="btn sm" onClick={() => setModal(f)}>Edit</button>
            <button className="btn sm" onClick={() => toggle(f)}>{f.is_active ? "Deactivate" : "Activate"}</button>
            <button className="btn sm danger" onClick={() => remove(f)}>Delete</button>
          </div>) },
      ]} />
      <Pagination page={page} pageSize={PAGE_SIZE} total={data?.total || 0} onChange={setPage} />
      {modal && <FormModal title={modal.id ? "Edit faculty" : "Add faculty"} fields={fields} initial={modal} onSubmit={save} onClose={() => setModal(null)} />}
      {assign && (
        <Modal title={`Assign courses – ${assign.full_name}`} onClose={() => setAssign(null)}>
          <div className="checklist">
            {(courses || []).map((c) => (
              <label key={c.id} className="check"><input type="checkbox" checked={picked.includes(c.id)}
                onChange={(e) => setPicked(e.target.checked ? [...picked, c.id] : picked.filter((x) => x !== c.id))} /> {c.name} <small className="muted">({c.department})</small></label>
            ))}
          </div>
          <div className="modal-actions"><button className="btn" onClick={() => setAssign(null)}>Cancel</button><button className="btn primary" onClick={saveAssign}>Save</button></div>
        </Modal>
      )}
    </>
  );
}
