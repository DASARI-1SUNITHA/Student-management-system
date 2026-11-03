import { useEffect, useState } from "react";
import useFetch from "../../hooks/useFetch";
import { DataTable, Modal, PageHeader, Pagination } from "../../components/common/ui";

export default function FacultyStudents() {
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");
  const [courseId, setCourseId] = useState("");
  const [view, setView] = useState(null);
  const { data: courses } = useFetch("/faculty/courses");
  const { data } = useFetch("/faculty/students", { page, page_size: 15, search: search || undefined, course_id: courseId || undefined });
  useEffect(() => { setPage(1); }, [search, courseId]);

  return (
    <>
      <PageHeader title="My Students" />
      <form className="filters" onSubmit={(e) => { e.preventDefault(); setSearch(q); }}>
        <input placeholder="Search name or ID" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={courseId} onChange={(e) => setCourseId(e.target.value)}>
          <option value="">All my courses</option>{(courses || []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <button className="btn">Search</button>
      </form>
      <DataTable rows={data?.items} columns={[
        { label: "ID", key: "student_code" }, { label: "Name", key: "full_name" }, { label: "Email", key: "email" },
        { label: "Course", key: "course" }, { label: "", render: (s) => <button className="btn sm" onClick={() => setView(s)}>Profile</button> }]} />
      <Pagination page={page} pageSize={15} total={data?.total || 0} onChange={setPage} />
      {view && (
        <Modal title="Student profile" onClose={() => setView(null)}>
          <dl className="details">{Object.entries({ "Student ID": view.student_code, Name: view.full_name, Email: view.email, Phone: view.phone, Department: view.department, Course: view.course })
            .map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v || "—"}</dd></div>)}</dl>
        </Modal>
      )}
    </>
  );
}
