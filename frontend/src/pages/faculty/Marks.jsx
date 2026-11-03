import { useEffect, useState } from "react";
import api, { errMsg } from "../../services/api";
import useFetch from "../../hooks/useFetch";
import { Badge, DataTable, FormModal, PageHeader, useToast } from "../../components/common/ui";

export default function Marks() {
  const notify = useToast();
  const [courseId, setCourseId] = useState("");
  const [examId, setExamId] = useState("");
  const [entries, setEntries] = useState({});
  const [newExam, setNewExam] = useState(false);
  const [busy, setBusy] = useState(false);

  const { data: courses } = useFetch("/faculty/courses");
  const course = (courses || []).find((c) => String(c.id) === courseId);
  const { data: exams, reload: reloadExams } = useFetch("/faculty/examinations", { course_id: courseId }, !!courseId);
  const { data: result, reload } = useFetch("/faculty/marks", { examination_id: examId }, !!examId);

  useEffect(() => {
    if (result) setEntries(Object.fromEntries(result.results.map((r) => [r.student_id, r.marks_obtained ?? ""])));
  }, [result]);

  const createExam = async (vals) => {
    try {
      const r = await api.post("/faculty/examinations", { ...vals, course_id: Number(courseId) });
      notify("Examination created"); setNewExam(false); await reloadExams(); setExamId(String(r.data.id));
    } catch (e) { notify(errMsg(e), "error"); }
  };

  const save = async () => {
    const list = Object.entries(entries).filter(([, v]) => v !== "").map(([id, v]) => ({ student_id: Number(id), marks_obtained: Number(v) }));
    if (!list.length) return notify("Enter at least one mark", "error");
    setBusy(true);
    try { await api.post("/faculty/marks", { examination_id: Number(examId), entries: list }); notify("Marks saved"); reload(); }
    catch (e) { notify(errMsg(e), "error"); } finally { setBusy(false); }
  };

  const max = result?.examination.max_marks;
  return (
    <>
      <PageHeader title="Marks & Grades">{courseId && <button className="btn primary" onClick={() => setNewExam(true)}>+ New examination</button>}</PageHeader>
      <div className="filters">
        <select value={courseId} onChange={(e) => { setCourseId(e.target.value); setExamId(""); }}>
          <option value="">Select course</option>{(courses || []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select value={examId} onChange={(e) => setExamId(e.target.value)} disabled={!courseId}>
          <option value="">Select examination</option>{(exams || []).map((x) => <option key={x.id} value={x.id}>{x.name} – {x.subject} (max {x.max_marks})</option>)}
        </select>
      </div>

      {result && (
        <section className="card">
          <h3>{result.examination.name} · maximum {max} marks</h3>
          <DataTable rows={result.results.map((r) => ({ ...r, id: r.student_id }))} columns={[
            { label: "ID", key: "student_code" }, { label: "Name", key: "student_name" },
            { label: `Marks (/${max})`, render: (r) => (
              <input className="mark-input" type="number" min="0" max={max} step="0.5" value={entries[r.student_id] ?? ""}
                onChange={(e) => setEntries({ ...entries, [r.student_id]: e.target.value })} />) },
            { label: "Saved %", render: (r) => (r.percentage == null ? "—" : `${r.percentage}%`) },
            { label: "Grade", render: (r) => (r.grade ? <Badge tone={r.grade === "F" ? "red" : "green"}>{r.grade}</Badge> : "—") }]}
            empty="No students are enrolled in this course" />
          <div className="modal-actions"><button className="btn primary" disabled={busy} onClick={save}>{busy ? "Saving…" : "Save marks"}</button></div>
        </section>
      )}

      {newExam && (
        <FormModal title="New examination" onClose={() => setNewExam(false)} onSubmit={createExam}
          fields={[
            { name: "name", label: "Exam name (e.g. Midterm)", required: true },
            { name: "subject_id", label: "Subject", type: "select", number: true, required: true, options: (course?.subjects || []).map((s) => [s.id, s.name]) },
            { name: "max_marks", label: "Maximum marks", type: "number", number: true, required: true, min: 1, step: "0.5" },
            { name: "exam_date", label: "Exam date", type: "date" }]} />
      )}
    </>
  );
}
