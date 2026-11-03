import { downloadFile, errMsg } from "../../services/api";
import { PageHeader, useToast } from "../../components/common/ui";

const REPORTS = [
  ["students", "Student report", "All students with department, course and account status."],
  ["attendance", "Attendance report", "Classes held, present count and attendance % per student and subject."],
  ["performance", "Academic performance report", "Every exam mark with percentage and grade."],
];

export default function Reports() {
  const notify = useToast();
  const get = async (key) => {
    try { await downloadFile(`/admin/reports/${key}`, `${key}-report.csv`); } catch (e) { notify(errMsg(e), "error"); }
  };
  return (
    <>
      <PageHeader title="Reports" />
      <p className="muted">Reports download as CSV files, which open directly in Excel.</p>
      <div className="grid-3">
        {REPORTS.map(([key, title, desc]) => (
          <div className="card" key={key}><h3>{title}</h3><p className="muted">{desc}</p><button className="btn primary" onClick={() => get(key)}>Download CSV</button></div>
        ))}
      </div>
    </>
  );
}
