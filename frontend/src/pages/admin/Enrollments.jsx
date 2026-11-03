import { useState } from "react";
import api, { errMsg } from "../../services/api";
import useFetch from "../../hooks/useFetch";
import { DataTable, PageHeader, useToast } from "../../components/common/ui";

export default function Enrollments() {
  const notify = useToast();
  const [courseId, setCourseId] = useState("");
  const [studentId, setStudentId] = useState("");
  const { data: courses } = useFetch("/courses");
  const { data: students } = useFetch("/admin/students", { page_size: 200 });
  const { data: enrolled, reload } = useFetch("/admin/enrollments", { course_id: courseId }, !!courseId);

  const add = async () => {
    try { await api.post("/admin/enrollments", { student_id: Number(studentId), course_id: Number(courseId) }); notify("Student enrolled"); setStudentId(""); reload(); }
    catch (e) { notify(errMsg(e), "error"); }
  };
  const remove = async (r) => {
    if (!window.confirm(`Remove ${r.full_name} from this course?`)) return;
    try { await api.delete(`/admin/enrollments/${r.enrollment_id}`); notify("Removed"); reload(); } catch (e) { notify(errMsg(e), "error"); }
  };

  return (
    <>
      <PageHeader title="Student Enrollments" />
      <div className="filters">
        <select value={courseId} onChange={(e) => setCourseId(e.target.value)}>
          <option value="">Select a course</option>{(courses || []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        {courseId && (<>
          <select value={studentId} onChange={(e) => setStudentId(e.target.value)}>
            <option value="">Select student to enroll</option>{(students?.items || []).map((s) => <option key={s.id} value={s.id}>{s.student_code} – {s.full_name}</option>)}
          </select>
          <button className="btn primary" disabled={!studentId} onClick={add}>Enroll</button>
        </>)}
      </div>
      {courseId && <DataTable rows={(enrolled || []).map((r) => ({ ...r, id: r.enrollment_id }))} columns={[
        { label: "Student ID", key: "student_code" }, { label: "Name", key: "full_name" },
        { label: "Actions", render: (r) => <button className="btn sm danger" onClick={() => remove(r)}>Remove</button> }]} />}
    </>
  );
}
