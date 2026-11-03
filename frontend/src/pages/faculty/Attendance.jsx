import { useState } from "react";
import api, { errMsg } from "../../services/api";
import useFetch from "../../hooks/useFetch";
import { Badge, DataTable, PageHeader, useToast } from "../../components/common/ui";

const today = () => new Date().toISOString().slice(0, 10);

export default function Attendance() {
  const notify = useToast();
  const [courseId, setCourseId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [date, setDate] = useState(today());
  const [roster, setRoster] = useState(null); // [{student_id, code, name, status}]
  const [busy, setBusy] = useState(false);

  const { data: courses } = useFetch("/faculty/courses");
  const course = (courses || []).find((c) => String(c.id) === courseId);
  const { data: summary, reload: reloadSummary } = useFetch("/faculty/attendance/summary", { course_id: courseId, subject_id: subjectId || undefined }, !!courseId);

  const load = async () => {
    try {
      const [st, existing] = await Promise.all([
        api.get("/faculty/students", { params: { course_id: courseId, page_size: 200 } }),
        api.get("/faculty/attendance", { params: { course_id: courseId, subject_id: subjectId, date } }),
      ]);
      const prev = Object.fromEntries(existing.data.map((a) => [a.student_id, a.status]));
      setRoster(st.data.items.map((s) => ({ student_id: s.id, code: s.student_code, name: s.full_name, status: prev[s.id] || "present" })));
      if (existing.data.length) notify("Existing attendance loaded – you can update it");
    } catch (e) { notify(errMsg(e), "error"); }
  };

  const setStatus = (id, status) => setRoster(roster.map((r) => (r.student_id === id ? { ...r, status } : r)));
  const setAll = (status) => setRoster(roster.map((r) => ({ ...r, status })));

  const save = async () => {
    setBusy(true);
    try {
      await api.post("/faculty/attendance", {
        course_id: Number(courseId), subject_id: Number(subjectId), date,
        records: roster.map((r) => ({ student_id: r.student_id, status: r.status })),
      });
      notify("Attendance saved"); reloadSummary();
    } catch (e) { notify(errMsg(e), "error"); } finally { setBusy(false); }
  };

  return (
    <>
      <PageHeader title="Attendance" />
      <div className="filters">
        <select value={courseId} onChange={(e) => { setCourseId(e.target.value); setSubjectId(""); setRoster(null); }}>
          <option value="">Select course</option>{(courses || []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select value={subjectId} onChange={(e) => { setSubjectId(e.target.value); setRoster(null); }} disabled={!course}>
          <option value="">Select subject</option>{(course?.subjects || []).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <input type="date" value={date} max={today()} onChange={(e) => { setDate(e.target.value); setRoster(null); }} />
        <button className="btn primary" disabled={!courseId || !subjectId || !date} onClick={load}>Load students</button>
      </div>

      {roster && (
        <section className="card">
          <div className="page-header"><h3>Mark attendance – {date}</h3>
            <div className="actions"><button className="btn sm" onClick={() => setAll("present")}>All present</button><button className="btn sm" onClick={() => setAll("absent")}>All absent</button></div></div>
          <DataTable rows={roster.map((r) => ({ ...r, id: r.student_id }))} columns={[
            { label: "ID", key: "code" }, { label: "Name", key: "name" },
            { label: "Status", render: (r) => (
              <div className="seg">
                <button className={r.status === "present" ? "on green" : ""} onClick={() => setStatus(r.student_id, "present")}>Present</button>
                <button className={r.status === "absent" ? "on red" : ""} onClick={() => setStatus(r.student_id, "absent")}>Absent</button>
              </div>) }]} empty="No students are enrolled in this course" />
          <div className="modal-actions"><button className="btn primary" disabled={busy || !roster.length} onClick={save}>{busy ? "Saving…" : "Save attendance"}</button></div>
        </section>
      )}

      {courseId && (
        <section className="card"><h3>Attendance summary {subjectId ? "(selected subject)" : "(all subjects)"}</h3>
          <DataTable rows={(summary || []).map((r) => ({ ...r, id: r.student_id }))} columns={[
            { label: "ID", key: "student_code" }, { label: "Name", key: "student_name" }, { label: "Present", key: "present" }, { label: "Classes", key: "total" },
            { label: "Attendance", render: (r) => <Badge tone={r.percentage >= 75 ? "green" : "red"}>{r.percentage}%</Badge> }]} empty="No attendance recorded yet" />
        </section>
      )}
    </>
  );
}
