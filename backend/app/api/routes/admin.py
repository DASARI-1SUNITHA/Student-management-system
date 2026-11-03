import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_roles
from app.core.security import hash_password
from app.database.session import get_db
from app.models import (
    Attendance, Course, Department, Enrollment, Examination, Faculty, FacultyCourse,
    Mark, Student, Subject, User,
)
from app.schemas.schemas import (
    AssignCoursesIn, EnrollIn, FacultyCreate, FacultyUpdate, StudentCreate, StudentUpdate,
)
from app.services.common import commit, grade_for, paginate, pct

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_roles("admin"))])


# ---------------- helpers ----------------
def check_dept_course(db: Session, department_id: int, course_id: int | None = None):
    if db.get(Department, department_id) is None:
        raise HTTPException(404, "Department not found")
    if course_id is not None:
        course = db.get(Course, course_id)
        if course is None:
            raise HTTPException(404, "Course not found")
        if course.department_id != department_id:
            raise HTTPException(400, "Course does not belong to the selected department")


def email_taken(db: Session, email: str, exclude_user_id: int | None = None) -> bool:
    stmt = select(User.id).where(User.email == email.lower())
    if exclude_user_id:
        stmt = stmt.where(User.id != exclude_user_id)
    return db.scalar(stmt) is not None


def student_out(s: Student) -> dict:
    return {
        "id": s.id, "student_code": s.student_code, "full_name": s.full_name,
        "email": s.user.email, "is_active": s.user.is_active, "phone": s.phone,
        "gender": s.gender, "date_of_birth": s.date_of_birth, "address": s.address,
        "department_id": s.department_id, "department": s.department.name,
        "course_id": s.course_id, "course": s.course.name,
        "admission_date": s.admission_date, "status": s.status,
    }


def faculty_out(f: Faculty, course_map: dict) -> dict:
    courses = course_map.get(f.id, [])
    return {
        "id": f.id, "faculty_code": f.faculty_code, "full_name": f.full_name,
        "email": f.user.email, "is_active": f.user.is_active, "phone": f.phone,
        "department_id": f.department_id, "department": f.department.name,
        "qualification": f.qualification, "designation": f.designation,
        "course_ids": [c.id for c in courses], "courses": [c.name for c in courses],
    }


def faculty_course_map(db: Session, faculty_ids: list[int]) -> dict:
    rows = db.execute(
        select(FacultyCourse.faculty_id, Course)
        .join(Course, Course.id == FacultyCourse.course_id)
        .where(FacultyCourse.faculty_id.in_(faculty_ids))
    ).all()
    out: dict = {}
    for fid, course in rows:
        out.setdefault(fid, []).append(course)
    return out


def set_faculty_courses(db: Session, faculty: Faculty, course_ids: list[int]):
    ids = set(course_ids)
    if ids and db.scalar(select(func.count(Course.id)).where(Course.id.in_(ids))) != len(ids):
        raise HTTPException(404, "One or more courses do not exist")
    existing = {fc.course_id: fc for fc in db.scalars(select(FacultyCourse).where(FacultyCourse.faculty_id == faculty.id))}
    for cid, fc in existing.items():
        if cid not in ids:
            db.delete(fc)
    for cid in ids - set(existing):
        db.add(FacultyCourse(faculty_id=faculty.id, course_id=cid))


def ensure_enrollment(db: Session, student_id: int, course_id: int):
    exists = db.scalar(select(Enrollment.id).where(Enrollment.student_id == student_id, Enrollment.course_id == course_id))
    if not exists:
        db.add(Enrollment(student_id=student_id, course_id=course_id))


# ---------------- students ----------------
@router.post("/students", status_code=201)
def create_student(p: StudentCreate, db: Session = Depends(get_db)):
    check_dept_course(db, p.department_id, p.course_id)
    if email_taken(db, p.email):
        raise HTTPException(409, "Email is already registered")
    if db.scalar(select(Student.id).where(Student.student_code == p.student_code)):
        raise HTTPException(409, "Student ID already exists")
    user = User(email=p.email.lower(), password_hash=hash_password(p.password), role="student")
    student = Student(user=user, **p.model_dump(exclude={"email", "password"}))
    db.add(student)
    db.flush()
    ensure_enrollment(db, student.id, p.course_id)
    commit(db)
    return student_out(student)


@router.get("/students")
def list_students(
    search: str | None = None, department_id: int | None = None, course_id: int | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=200), db: Session = Depends(get_db),
):
    stmt = (
        select(Student).join(User, User.id == Student.user_id)
        .options(joinedload(Student.user), joinedload(Student.department), joinedload(Student.course))
        .order_by(Student.id.desc())
    )
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(or_(Student.full_name.ilike(like), Student.student_code.ilike(like), User.email.ilike(like)))
    if department_id:
        stmt = stmt.where(Student.department_id == department_id)
    if course_id:
        stmt = stmt.where(Student.course_id == course_id)
    total, items = paginate(db, stmt, page, page_size)
    return {"items": [student_out(s) for s in items], "total": total, "page": page, "page_size": page_size}


@router.get("/students/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db)):
    s = db.get(Student, student_id)
    if s is None:
        raise HTTPException(404, "Student not found")
    return student_out(s)


@router.put("/students/{student_id}")
def update_student(student_id: int, p: StudentUpdate, db: Session = Depends(get_db)):
    s = db.get(Student, student_id)
    if s is None:
        raise HTTPException(404, "Student not found")
    data = p.model_dump(exclude_unset=True)
    is_active = data.pop("is_active", None)
    email = data.pop("email", None)
    check_dept_course(db, data.get("department_id", s.department_id), data.get("course_id", s.course_id))
    if email:
        if email_taken(db, email, s.user_id):
            raise HTTPException(409, "Email is already registered")
        s.user.email = email.lower()
    if is_active is not None:
        s.user.is_active = is_active
    for k, v in data.items():
        setattr(s, k, v)
    if "course_id" in data:
        ensure_enrollment(db, s.id, data["course_id"])
    commit(db)
    return student_out(s)


@router.delete("/students/{student_id}", status_code=204)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    s = db.get(Student, student_id)
    if s is None:
        raise HTTPException(404, "Student not found")
    db.delete(s.user)  # cascades to student; DB cascades enrollments, attendance, marks
    commit(db)


# ---------------- faculty ----------------
@router.post("/faculty", status_code=201)
def create_faculty(p: FacultyCreate, db: Session = Depends(get_db)):
    check_dept_course(db, p.department_id)
    if email_taken(db, p.email):
        raise HTTPException(409, "Email is already registered")
    if db.scalar(select(Faculty.id).where(Faculty.faculty_code == p.faculty_code)):
        raise HTTPException(409, "Faculty ID already exists")
    user = User(email=p.email.lower(), password_hash=hash_password(p.password), role="faculty")
    fac = Faculty(user=user, **p.model_dump(exclude={"email", "password", "course_ids"}))
    db.add(fac)
    db.flush()
    set_faculty_courses(db, fac, p.course_ids)
    commit(db)
    return faculty_out(fac, faculty_course_map(db, [fac.id]))


@router.get("/faculty")
def list_faculty(
    search: str | None = None, department_id: int | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=200), db: Session = Depends(get_db),
):
    stmt = (
        select(Faculty).join(User, User.id == Faculty.user_id)
        .options(joinedload(Faculty.user), joinedload(Faculty.department)).order_by(Faculty.id.desc())
    )
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(or_(Faculty.full_name.ilike(like), Faculty.faculty_code.ilike(like), User.email.ilike(like)))
    if department_id:
        stmt = stmt.where(Faculty.department_id == department_id)
    total, items = paginate(db, stmt, page, page_size)
    cmap = faculty_course_map(db, [f.id for f in items])
    return {"items": [faculty_out(f, cmap) for f in items], "total": total, "page": page, "page_size": page_size}


@router.put("/faculty/{faculty_id}")
def update_faculty(faculty_id: int, p: FacultyUpdate, db: Session = Depends(get_db)):
    f = db.get(Faculty, faculty_id)
    if f is None:
        raise HTTPException(404, "Faculty not found")
    data = p.model_dump(exclude_unset=True)
    is_active = data.pop("is_active", None)
    email = data.pop("email", None)
    if "department_id" in data:
        check_dept_course(db, data["department_id"])
    if email:
        if email_taken(db, email, f.user_id):
            raise HTTPException(409, "Email is already registered")
        f.user.email = email.lower()
    if is_active is not None:
        f.user.is_active = is_active
    for k, v in data.items():
        setattr(f, k, v)
    commit(db)
    return faculty_out(f, faculty_course_map(db, [f.id]))


@router.post("/faculty/{faculty_id}/courses")
def assign_courses(faculty_id: int, p: AssignCoursesIn, db: Session = Depends(get_db)):
    f = db.get(Faculty, faculty_id)
    if f is None:
        raise HTTPException(404, "Faculty not found")
    set_faculty_courses(db, f, p.course_ids)
    commit(db)
    return faculty_out(f, faculty_course_map(db, [f.id]))


@router.delete("/faculty/{faculty_id}", status_code=204)
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    f = db.get(Faculty, faculty_id)
    if f is None:
        raise HTTPException(404, "Faculty not found")
    db.delete(f.user)
    commit(db)


# ---------------- enrollments ----------------
@router.get("/enrollments")
def list_enrollments(course_id: int, db: Session = Depends(get_db)):
    rows = db.execute(
        select(Enrollment.id, Student).join(Student, Student.id == Enrollment.student_id)
        .where(Enrollment.course_id == course_id).order_by(Student.student_code)
    ).all()
    return [{"enrollment_id": eid, "student_id": s.id, "student_code": s.student_code, "full_name": s.full_name} for eid, s in rows]


@router.post("/enrollments", status_code=201)
def enroll(p: EnrollIn, db: Session = Depends(get_db)):
    if db.get(Student, p.student_id) is None or db.get(Course, p.course_id) is None:
        raise HTTPException(404, "Student or course not found")
    if db.scalar(select(Enrollment.id).where(Enrollment.student_id == p.student_id, Enrollment.course_id == p.course_id)):
        raise HTTPException(409, "Student is already enrolled in this course")
    db.add(Enrollment(student_id=p.student_id, course_id=p.course_id))
    commit(db)
    return {"message": "Student enrolled"}


@router.delete("/enrollments/{enrollment_id}", status_code=204)
def unenroll(enrollment_id: int, db: Session = Depends(get_db)):
    e = db.get(Enrollment, enrollment_id)
    if e is None:
        raise HTTPException(404, "Enrollment not found")
    db.delete(e)
    commit(db)


# ---------------- dashboard ----------------
def _marks_pct_expr():
    return Mark.marks_obtained * 100.0 / Examination.max_marks


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    count = lambda col, *where: db.scalar(select(func.count(col)).where(*where)) or 0  # noqa: E731
    att_total = count(Attendance.id)
    att_present = count(Attendance.id, Attendance.status == "present")
    avg_marks = db.scalar(select(func.avg(_marks_pct_expr())).select_from(Mark).join(Examination, Examination.id == Mark.examination_id))
    perf = db.execute(
        select(Course.name, func.avg(_marks_pct_expr()))
        .select_from(Mark).join(Examination, Examination.id == Mark.examination_id)
        .join(Course, Course.id == Examination.course_id).group_by(Course.name).order_by(Course.name)
    ).all()
    recent = db.scalars(
        select(Student).options(joinedload(Student.user), joinedload(Student.department), joinedload(Student.course))
        .order_by(Student.id.desc()).limit(5)
    ).all()
    return {
        "total_students": count(Student.id),
        "active_students": count(User.id, User.role == "student", User.is_active.is_(True)),
        "total_faculty": count(Faculty.id),
        "total_departments": count(Department.id),
        "total_courses": count(Course.id),
        "attendance": {"total_records": att_total, "present": att_present, "absent": att_total - att_present, "percentage": pct(att_present, att_total)},
        "average_marks_percentage": round(avg_marks or 0, 2),
        "course_performance": [{"course": n, "average_percentage": round(a or 0, 2)} for n, a in perf],
        "recent_registrations": [student_out(s) for s in recent],
    }


# ---------------- reports (CSV, opens in Excel) ----------------
def csv_response(name: str, header: list[str], rows) -> Response:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    return Response(
        "\ufeff" + buf.getvalue(), media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{name}-{date.today()}.csv"'},
    )


@router.get("/reports/students")
def report_students(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Student).options(joinedload(Student.user), joinedload(Student.department), joinedload(Student.course)).order_by(Student.student_code)
    ).all()
    return csv_response(
        "students-report",
        ["Student ID", "Name", "Email", "Phone", "Department", "Course", "Admission date", "Status", "Account active"],
        [[s.student_code, s.full_name, s.user.email, s.phone, s.department.name, s.course.name, s.admission_date, s.status, s.user.is_active] for s in rows],
    )


@router.get("/reports/attendance")
def report_attendance(db: Session = Depends(get_db)):
    rows = db.execute(
        select(
            Student.student_code, Student.full_name, Course.name, Subject.name,
            func.count(Attendance.id),
            func.sum(case((Attendance.status == "present", 1), else_=0)),
        )
        .select_from(Attendance).join(Student, Student.id == Attendance.student_id)
        .join(Course, Course.id == Attendance.course_id).join(Subject, Subject.id == Attendance.subject_id)
        .group_by(Student.student_code, Student.full_name, Course.name, Subject.name)
        .order_by(Student.student_code, Subject.name)
    ).all()
    return csv_response(
        "attendance-report",
        ["Student ID", "Name", "Course", "Subject", "Classes held", "Present", "Attendance %"],
        [[c, n, co, su, t, int(p or 0), pct(p or 0, t)] for c, n, co, su, t, p in rows],
    )


@router.get("/reports/performance")
def report_performance(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Student.student_code, Student.full_name, Course.name, Subject.name, Examination.name, Mark.marks_obtained, Examination.max_marks)
        .select_from(Mark).join(Student, Student.id == Mark.student_id)
        .join(Examination, Examination.id == Mark.examination_id)
        .join(Course, Course.id == Examination.course_id).join(Subject, Subject.id == Examination.subject_id)
        .order_by(Student.student_code, Examination.name)
    ).all()
    return csv_response(
        "performance-report",
        ["Student ID", "Name", "Course", "Subject", "Exam", "Marks", "Max marks", "Percentage", "Grade"],
        [[c, n, co, su, ex, m, mx, pct(m, mx), grade_for(pct(m, mx))] for c, n, co, su, ex, m, mx in rows],
    )
