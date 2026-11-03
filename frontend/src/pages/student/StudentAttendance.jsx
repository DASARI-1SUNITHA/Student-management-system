import useFetch from "../../hooks/useFetch";
import { Badge, DataTable, Loading, PageHeader, StatCard } from "../../components/common/ui";

export default function StudentAttendance() {
  const { data: d, loading, error } = useFetch("/student/attendance");
  if (loading || error) return <Loading error={error} />;
  return (
    <>
      <PageHeader title="My Attendance" />
      <div className="stats">
        <StatCard label="Overall" value={`${d.overall.percentage}%`} />
        <StatCard label="Present" value={d.overall.present} />
        <StatCard label="Absent" value={d.overall.absent} />
        <StatCard label="Total classes" value={d.overall.total} />
      </div>
      <section className="card"><h3>Subject-wise</h3>
        <DataTable rows={d.subject_wise.map((s) => ({ ...s, id: s.subject }))} columns={[{ label: "Subject", key: "subject" }, { label: "Present", key: "present" }, { label: "Total", key: "total" },
          { label: "Percentage", render: (s) => <Badge tone={s.percentage >= 75 ? "green" : "red"}>{s.percentage}%</Badge> }]} />
      </section>
      <section className="card"><h3>Daily records</h3>
        <DataTable rows={d.records.map((r, i) => ({ ...r, id: i }))} columns={[{ label: "Date", key: "date" }, { label: "Subject", key: "subject" },
          { label: "Status", render: (r) => <Badge tone={r.status === "present" ? "green" : "red"}>{r.status}</Badge> }]} />
      </section>
    </>
  );
}
