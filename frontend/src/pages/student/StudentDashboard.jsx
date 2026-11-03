import useFetch from "../../hooks/useFetch";
import { Badge, DataTable, Loading, PageHeader, StatCard } from "../../components/common/ui";

export default function StudentDashboard() {
  const { data: d, loading, error } = useFetch("/student/dashboard");
  if (loading || error) return <Loading error={error} />;
  const p = d.profile;
  return (
    <>
      <PageHeader title={`Welcome, ${p.full_name}`} />
      <div className="stats">
        <StatCard label="Student ID" value={p.student_code} sub={p.status} />
        <StatCard label="Department" value={p.department} sub={p.course} />
        <StatCard label="Attendance" value={`${d.attendance.percentage}%`} sub={`${d.attendance.present} of ${d.attendance.total} classes`} />
        <StatCard label="Overall result" value={`${d.marks_summary.percentage}%`} sub={d.marks_summary.grade ? `Grade ${d.marks_summary.grade}` : "No results yet"} />
        <StatCard label="Enrolled courses" value={d.enrolled_courses.length} />
      </div>
      {d.attendance.total > 0 && d.attendance.percentage < 75 && <div className="alert">Your attendance is below 75%. Please attend more classes.</div>}
      <div className="grid-2">
        <section className="card"><h3>Recent results</h3>
          <DataTable rows={d.recent_results} columns={[{ label: "Exam", key: "exam" }, { label: "Subject", key: "subject" },
            { label: "Marks", render: (r) => `${r.marks_obtained}/${r.max_marks}` }, { label: "Grade", render: (r) => <Badge tone={r.grade === "F" ? "red" : "green"}>{r.grade}</Badge> }]} />
        </section>
        <section className="card"><h3>Recent attendance</h3>
          <DataTable rows={d.recent_attendance} columns={[{ label: "Date", key: "date" }, { label: "Subject", key: "subject" },
            { label: "Status", render: (r) => <Badge tone={r.status === "present" ? "green" : "red"}>{r.status}</Badge> }]} />
        </section>
      </div>
    </>
  );
}
