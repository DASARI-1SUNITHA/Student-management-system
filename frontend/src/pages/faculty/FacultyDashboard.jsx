import useFetch from "../../hooks/useFetch";
import { DataTable, Loading, PageHeader, StatCard } from "../../components/common/ui";

export default function FacultyDashboard() {
  const { data: d, loading, error } = useFetch("/faculty/dashboard");
  if (loading || error) return <Loading error={error} />;
  return (
    <>
      <PageHeader title="Faculty Dashboard" />
      <div className="stats">
        <StatCard label="Assigned courses" value={d.courses.length} />
        <StatCard label="Enrolled students" value={d.total_students} />
        <StatCard label="Attendance" value={`${d.attendance.percentage}%`} sub={`${d.attendance.present} of ${d.attendance.total_records} present`} />
        <StatCard label="Average marks" value={`${d.average_marks_percentage}%`} />
      </div>
      <div className="grid-2">
        <section className="card"><h3>My courses</h3>
          <DataTable rows={d.courses} columns={[{ label: "Course", key: "name" }, { label: "Students", key: "enrolled_students" },
            { label: "Subjects", render: (c) => c.subjects.map((s) => s.name).join(", ") || "—" }]} />
        </section>
        <section className="card"><h3>Recent attendance sessions</h3>
          <DataTable rows={d.recent_activities} columns={[{ label: "Date", key: "date" }, { label: "Course", key: "course" }, { label: "Subject", key: "subject" }, { label: "Marked", key: "students_marked" }]} />
        </section>
      </div>
    </>
  );
}
