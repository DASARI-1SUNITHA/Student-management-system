import useFetch from "../../hooks/useFetch";
import { Loading, PageHeader } from "../../components/common/ui";

export default function StudentCourses() {
  const { data, loading, error } = useFetch("/student/courses");
  if (loading || error) return <Loading error={error} />;
  return (
    <>
      <PageHeader title="My Courses" />
      {data.length === 0 && <p className="muted">You are not enrolled in any course yet.</p>}
      <div className="grid-2">
        {data.map((c) => (
          <section className="card" key={c.id}>
            <h3>{c.name} <small className="muted">({c.code})</small></h3>
            <p className="muted">{c.department}</p>
            <h4>Subjects</h4><ul>{c.subjects.map((s) => <li key={s}>{s}</li>)}{!c.subjects.length && <li className="muted">None yet</li>}</ul>
            <h4>Faculty</h4><ul>{c.faculty.map((f) => <li key={f.email}>{f.name} – {f.designation || "Faculty"} ({f.email})</li>)}{!c.faculty.length && <li className="muted">Not assigned yet</li>}</ul>
          </section>
        ))}
      </div>
    </>
  );
}
