import useFetch from "../../hooks/useFetch";
import { Badge, DataTable, Loading, PageHeader, StatCard } from "../../components/common/ui";

export default function StudentMarks() {
  const { data: d, loading, error } = useFetch("/student/marks");
  if (loading || error) return <Loading error={error} />;
  const s = d.summary;
  return (
    <>
      <PageHeader title="My Marks & Grades" />
      <div className="stats">
        <StatCard label="Total marks" value={`${s.total_obtained} / ${s.total_max}`} />
        <StatCard label="Percentage" value={`${s.percentage}%`} />
        <StatCard label="Overall grade" value={s.grade || "—"} />
      </div>
      <section className="card"><h3>Examination results</h3>
        <DataTable rows={d.results.map((r, i) => ({ ...r, id: i }))} columns={[
          { label: "Exam", key: "exam" }, { label: "Subject", key: "subject" }, { label: "Date", key: "exam_date" },
          { label: "Marks", render: (r) => `${r.marks_obtained} / ${r.max_marks}` }, { label: "%", render: (r) => `${r.percentage}%` },
          { label: "Grade", render: (r) => <Badge tone={r.grade === "F" ? "red" : "green"}>{r.grade}</Badge> }]} empty="No results published yet" />
      </section>
    </>
  );
}
