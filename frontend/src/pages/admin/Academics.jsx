import useFetch from "../../hooks/useFetch";
import { CrudPage } from "../../components/common/ui";

export function Departments() {
  return (
    <CrudPage title="Departments" endpoint="/departments"
      columns={[{ label: "Code", key: "code" }, { label: "Name", key: "name" }]}
      fields={[{ name: "name", label: "Name", required: true }, { name: "code", label: "Code", required: true }]} />
  );
}

export function Courses() {
  const { data: depts } = useFetch("/departments");
  return (
    <CrudPage title="Courses" endpoint="/courses"
      columns={[{ label: "Code", key: "code" }, { label: "Name", key: "name" }, { label: "Department", key: "department" }, { label: "Credits", key: "credits" }]}
      fields={[
        { name: "name", label: "Name", required: true }, { name: "code", label: "Code", required: true },
        { name: "credits", label: "Credits", type: "number", number: true, min: 1, required: true },
        { name: "department_id", label: "Department", type: "select", number: true, required: true, options: (depts || []).map((d) => [d.id, d.name]) },
      ]} initialNew={{ credits: 3 }} />
  );
}

export function Subjects() {
  const { data: courses } = useFetch("/courses");
  return (
    <CrudPage title="Subjects" endpoint="/subjects"
      columns={[{ label: "Code", key: "code" }, { label: "Name", key: "name" }, { label: "Course", key: "course" }]}
      fields={[
        { name: "name", label: "Name", required: true }, { name: "code", label: "Code", required: true },
        { name: "course_id", label: "Course", type: "select", number: true, required: true, options: (courses || []).map((c) => [c.id, c.name]) },
      ]} />
  );
}
