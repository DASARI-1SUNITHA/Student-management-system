import useFetch from "../../hooks/useFetch";
import { DataTable, Loading, PageHeader, StatCard } from "../../components/common/ui";

export default function AdminDashboard() {
  const { data: d, loading, error } = useFetch("/admin/dashboard");
  if (loading || error) return <Loading error={error} />;
  return (
    <>
      <PageHeader title="Admin Dashboard" />
      <div className="stats">
        <StatCard label="Total students" value={d.total_students} sub={`${d.active_students} active`} />
        <StatCard label="Total faculty" value={d.total_faculty} />
        <StatCard label="Departments" value={d.total_departments} />
        <StatCard label="Courses" value={d.total_courses} />
        <StatCard label="Attendance" value={`${d.attendance.percentage}%`} sub={`${d.attendance.present} present / ${d.attendance.absent} absent`} />
        <StatCard label="Average marks" value={`${d.average_marks_percentage}%`} />
      </div>
      <div className="grid-2">
        <section className="card"><h3>Course performance</h3>
          {d.course_performance.length ? d.course_performance.map((c) => (
            <div key={c.course} className="bar-row"><span>{c.course}</span><div className="bar"><i style={{ width: `${c.average_percentage}%` }} /></div><b>{c.average_percentage}%</b></div>
          )) : <p className="muted">No marks entered yet.</p>}
        </section>
        <section className="card"><h3>Recent registrations</h3>
          <DataTable rows={d.recent_registrations} columns={[
            { label: "ID", key: "student_code" }, { label: "Name", key: "full_name" }, { label: "Course", key: "course" }]} />
        </section>
      </div>
    </>
  );
}
