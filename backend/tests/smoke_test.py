"""End-to-end API check using a throw-away SQLite file (never touches Neon).
Run from the backend folder:  python -m tests.smoke_test
"""
import os

os.environ["DATABASE_URL"] = "sqlite:///./smoke_test.db"
os.environ["SECRET_KEY"] = "test-secret-key-test-secret-key-1234"
if os.path.exists("smoke_test.db"):
    os.remove("smoke_test.db")

from datetime import date  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402

Base.metadata.create_all(engine)
with SessionLocal() as db:
    db.add(User(email="admin@test.com", password_hash=hash_password("AdminPass#1"), role="admin"))
    db.commit()

c = TestClient(app)
checks = []


def check(name, cond):
    checks.append(cond)
    print(("PASS" if cond else "FAIL"), name)


def login(email, pw, role=None):
    r = c.post("/auth/login", json={"email": email, "password": pw, "role": role})
    return r, {"Authorization": f"Bearer {r.json().get('access_token', '')}"}


r, A = login("admin@test.com", "AdminPass#1", "admin")
check("admin login", r.status_code == 200 and r.json()["user"]["role"] == "admin")
check("wrong password rejected", login("admin@test.com", "nope")[0].status_code == 401)
check("wrong portal rejected", login("admin@test.com", "AdminPass#1", "student")[0].status_code == 401)
check("no token -> 401", c.get("/admin/dashboard").status_code == 401)

d = c.post("/departments", json={"name": "Computer Science", "code": "cse"}, headers=A).json()
co = c.post("/courses", json={"name": "BTech CSE", "code": "btcse", "department_id": d["id"]}, headers=A).json()
c2 = c.post("/courses", json={"name": "BTech ECE", "code": "btece", "department_id": d["id"]}, headers=A).json()
s1 = c.post("/subjects", json={"name": "Databases", "code": "cs202", "course_id": co["id"]}, headers=A).json()
check("duplicate dept -> 409", c.post("/departments", json={"name": "Computer Science", "code": "X"}, headers=A).status_code == 409)

stu = lambda code, email: {"student_code": code, "full_name": "Student " + code, "email": email, "password": "Student#123",  # noqa: E731
                           "phone": "9876543210", "department_id": d["id"], "course_id": co["id"], "admission_date": str(date.today())}
r1 = c.post("/admin/students", json=stu("S1", "s1@test.com"), headers=A)
r2 = c.post("/admin/students", json=stu("S2", "s2@test.com"), headers=A)
check("create students", r1.status_code == 201 and r2.status_code == 201)
check("duplicate student id -> 409", c.post("/admin/students", json=stu("S1", "other@test.com"), headers=A).status_code == 409)
check("duplicate email -> 409", c.post("/admin/students", json=stu("S9", "s1@test.com"), headers=A).status_code == 409)
check("bad phone -> 422", c.post("/admin/students", json={**stu("S8", "x@test.com"), "phone": "abc"}, headers=A).status_code == 422)
sid1, sid2 = r1.json()["id"], r2.json()["id"]

f = c.post("/admin/faculty", json={"faculty_code": "F1", "full_name": "Dr Rao", "email": "f1@test.com", "password": "Faculty#123",
                                   "department_id": d["id"], "course_ids": [co["id"]]}, headers=A)
check("create faculty with course", f.status_code == 201 and f.json()["course_ids"] == [co["id"]])
check("list students search", c.get("/admin/students?search=S1", headers=A).json()["total"] == 1)

_, F = login("f1@test.com", "Faculty#123", "faculty")
_, S1 = login("s1@test.com", "Student#123", "student")
_, S2 = login("s2@test.com", "Student#123", "student")

check("student blocked from admin API", c.get("/admin/students", headers=S1).status_code == 403)
check("faculty blocked from admin API", c.get("/admin/students", headers=F).status_code == 403)
check("faculty cannot create dept", c.post("/departments", json={"name": "Hack", "code": "H"}, headers=F).status_code == 403)
check("faculty sees enrolled students", c.get("/faculty/students", headers=F).json()["total"] == 2)
check("faculty unassigned course -> 403", c.get(f"/faculty/students?course_id={c2['id']}", headers=F).status_code == 403)

today = str(date.today())
att = {"course_id": co["id"], "subject_id": s1["id"], "date": today,
       "records": [{"student_id": sid1, "status": "present"}, {"student_id": sid2, "status": "absent"}]}
check("mark attendance", c.post("/faculty/attendance", json=att, headers=F).json()["saved"] == 2)
att["records"][1]["status"] = "present"
c.post("/faculty/attendance", json=att, headers=F)
check("re-marking updates (no duplicates)", len(c.get(f"/faculty/attendance?course_id={co['id']}", headers=F).json()) == 2)
check("student sees own attendance", c.get("/student/attendance", headers=S1).json()["overall"]["percentage"] == 100.0)

ex = c.post("/faculty/examinations", json={"name": "Midterm", "course_id": co["id"], "subject_id": s1["id"], "max_marks": 50}, headers=F).json()
check("marks above max rejected", c.post("/faculty/marks", json={"examination_id": ex["id"], "entries": [{"student_id": sid1, "marks_obtained": 99}]}, headers=F).status_code == 400)
check("save marks", c.post("/faculty/marks", json={"examination_id": ex["id"], "entries": [{"student_id": sid1, "marks_obtained": 45}, {"student_id": sid2, "marks_obtained": 20}]}, headers=F).json()["saved"] == 2)
m = c.get(f"/faculty/marks?examination_id={ex['id']}", headers=F).json()["results"]
row1 = next(x for x in m if x["student_id"] == sid1)
check("percentage and grade", row1["percentage"] == 90.0 and row1["grade"] == "A+")
check("update mark with right version", c.put(f"/faculty/marks/{row1['mark_id']}", json={"marks_obtained": 40, "version": row1["version"]}, headers=F).status_code == 200)
check("stale version -> 409", c.put(f"/faculty/marks/{row1['mark_id']}", json={"marks_obtained": 41, "version": row1["version"]}, headers=F).status_code == 409)
mk = c.get("/student/marks", headers=S1).json()
check("student sees own marks only", len(mk["results"]) == 1 and mk["results"][0]["marks_obtained"] == 40)
check("student cannot save marks", c.post("/faculty/marks", json={"examination_id": ex["id"], "entries": [{"student_id": sid1, "marks_obtained": 50}]}, headers=S1).status_code == 403)
check("student cannot view other student (no such route)", c.get(f"/faculty/students/{sid2}", headers=S1).status_code == 403)

check("student updates phone", c.put("/student/profile", json={"phone": "9123456789"}, headers=S1).json()["phone"] == "9123456789")
c.put("/student/profile", json={"student_code": "HACK", "course_id": 99}, headers=S1)
check("student cannot change student ID", c.get("/student/profile", headers=S1).json()["student_code"] == "S1")
check("student dashboard", c.get("/student/dashboard", headers=S2).json()["profile"]["student_code"] == "S2")
check("student courses show faculty", c.get("/student/courses", headers=S1).json()[0]["faculty"][0]["name"] == "Dr Rao")
check("faculty dashboard", c.get("/faculty/dashboard", headers=F).json()["total_students"] == 2)

dash = c.get("/admin/dashboard", headers=A).json()
check("admin dashboard live numbers", dash["total_students"] == 2 and dash["total_faculty"] == 1 and dash["attendance"]["total_records"] == 2)
for name in ("students", "attendance", "performance"):
    r = c.get(f"/admin/reports/{name}", headers=A)
    check(f"csv report {name}", r.status_code == 200 and "text/csv" in r.headers["content-type"])

check("change password", c.post("/auth/change-password", json={"current_password": "Student#123", "new_password": "NewStudent#456"}, headers=S1).status_code == 200)
check("new password works", login("s1@test.com", "NewStudent#456")[0].status_code == 200)

c.put(f"/admin/students/{sid2}", json={"is_active": False}, headers=A)
check("deactivated student cannot log in", login("s2@test.com", "Student#123")[0].status_code == 403)
check("deactivated student's old token dies", c.get("/student/profile", headers=S2).status_code == 401)
check("delete student", c.delete(f"/admin/students/{sid2}", headers=A).status_code == 204)
check("dept in use cannot be deleted", c.delete(f"/departments/{d['id']}", headers=A).status_code == 409)

print(f"\n{sum(checks)}/{len(checks)} checks passed")
os.remove("smoke_test.db")
raise SystemExit(0 if all(checks) else 1)
