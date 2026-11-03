from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import accessible_course_ids, assert_course_access, require_roles
from app.database.session import get_db
from app.models import (
    Attendance, Course, Enrollment, Examination, Mark, Student, Subject, User,
)
from app.schemas.schemas import AttendanceIn, ExamIn, MarkUpdateIn, MarksBulkIn
from app.services.common import commit, grade_for, paginate, pct

router = APIRouter(prefix="/faculty", tags=["Faculty"])
staff = require_roles("faculty", "admin")  # admin may use these screens too; faculty are limited to assigned courses


def _fac_id(user: User):
    return user.faculty.id if user.faculty else None


def _enrolled_ids(db: Session, course_id: int) -> set[int]:
    return set(db.scalars(select(Enrollment.student_id).where(Enrollment.course_id == course_id)))


def _present_sum():
    return func.sum(case((Attendance.status == "present", 1), else_=0))


# ---------------- courses ----------------
@router.get("/courses")
def my_courses(db: Session = Depends(get_db), user: User = Depends(staff)):
    ids = accessible_course_ids(db, user)
    stmt = select(Course).options(joinedload(Course.department)).order_by(Course.name)
    if ids is not None:
        stmt = stmt.where(Course.id.in_(ids))
    courses = db.scalars(stmt).all()
    cids = [c.id for c in courses]
    subs: dict = {}
    for s in db.scalars(select(Subject).where(Subject.course_id.in_(cids)).order_by(Subject.name)):
        subs.setdefault(s.course_id, []).append({"id": s.id, "name": s.name, "code": s.code})
    counts = dict(db.execute(select(Enrollment.course_id, func.count()).where(Enrollment.course_id.in_(cids)).group_by(Enrollment.course_id)).all())
    return [
        {"id": c.id, "name": c.name, "code": c.code, "department": c.department.name,
         "enrolled_students": counts.get(c.id, 0), "subjects": subs.get(c.id, [])}
        for c in courses
    ]


# ---------------- dashboard ----------------
@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles("faculty"))):
    ids = accessible_course_ids(db, user)
    total_students = db.scalar(select(func.count(func.distinct(Enrollment.student_id))).where(Enrollment.course_id.in_(ids))) or 0
    att_total, att_present = db.execute(
        select(func.count(Attendance.id), _present_sum()).where(Attendance.course_id.in_(ids))
    ).one()
    avg = db.scalar(
        select(func.avg(Mark.marks_obtained * 100.0 / Examination.max_marks))
        .select_from(Mark).join(Examination, Examination.id == Mark.examination_id).where(Examination.course_id.in_(ids))
    )
    recent = db.execute(
        select(Attendance.date, Course.name, Subject.name, func.count(Attendance.id))
        .join(Course, Course.id == Attendance.course_id).join(Subject, Subject.id == Attendance.subject_id)
        .where(Attendance.course_id.in_(ids)).group_by(Attendance.date, Course.name, Subject.name)
        .order_by(Attendance.date.desc()).limit(5)
    ).all()
    return {
        "courses": my_courses(db, user),
        "total_students": total_students,
        "attendance": {"total_records": att_total, "present": int(att_present or 0), "percentage": pct(att_present or 0, att_total)},
        "average_marks_percentage": round(avg or 0, 2),
        "recent_activities": [{"date": d, "course": c, "subject": s, "students_marked": n} for d, c, s, n in recent],
    }


# ---------------- students ----------------
def _student_row(s: Student) -> dict:
    # Faculty see only non-sensitive fields (no address, DOB, account status)
    return {"id": s.id, "student_code": s.student_code, "full_name": s.full_name, "email": s.user.email,
            "phone": s.phone, "gender": s.gender, "department": s.department.name, "course": s.course.name}


@router.get("/students")
def my_students(
    course_id: int | None = None, search: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db), user: User = Depends(staff),
):
    if course_id is not None:
        assert_course_access(db, user, course_id)
    ids = [course_id] if course_id else accessible_course_ids(db, user)
    sub = select(Enrollment.student_id)
    if ids is not None:
        sub = sub.where(Enrollment.course_id.in_(ids))
    stmt = (
        select(Student).join(User, User.id == Student.user_id)
        .options(joinedload(Student.user), joinedload(Student.department), joinedload(Student.course))
        .where(Student.id.in_(sub)).order_by(Student.student_code)
    )
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(or_(Student.full_name.ilike(like), Student.student_code.ilike(like)))
    total, items = paginate(db, stmt, page, page_size)
    return {"items": [_student_row(s) for s in items], "total": total, "page": page, "page_size": page_size}


@router.get("/students/{student_id}")
def student_profile(student_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    s = db.get(Student, student_id)
    ids = accessible_course_ids(db, user)
    shared = select(Enrollment.id).where(Enrollment.student_id == student_id)
    if ids is not None:
        shared = shared.where(Enrollment.course_id.in_(ids))
    # same 404 whether the student does not exist or is not yours (prevents probing)
    if s is None or db.scalar(shared.limit(1)) is None:
        raise HTTPException(404, "Student not found in your courses")
    return _student_row(s)


# ---------------- attendance ----------------
@router.post("/attendance")
def mark_attendance(p: AttendanceIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    assert_course_access(db, user, p.course_id)
    subject = db.get(Subject, p.subject_id)
    if subject is None or subject.course_id != p.course_id:
        raise HTTPException(400, "Subject does not belong to this course")
    if p.date > date_type.today():
        raise HTTPException(400, "Cannot mark attendance for a future date")
    wanted = {r.student_id: r.status for r in p.records}  # de-duplicates repeated students
    if not set(wanted) <= _enrolled_ids(db, p.course_id):
        raise HTTPException(400, "One or more students are not enrolled in this course")
    existing = {
        a.student_id: a for a in db.scalars(
            select(Attendance).where(Attendance.subject_id == p.subject_id, Attendance.date == p.date, Attendance.student_id.in_(list(wanted)))
        )
    }
    for sid, status in wanted.items():
        if sid in existing:
            existing[sid].status, existing[sid].faculty_id = status, _fac_id(user)
        else:
            db.add(Attendance(student_id=sid, course_id=p.course_id, subject_id=p.subject_id,
                              faculty_id=_fac_id(user), date=p.date, status=status))
    commit(db)  # the unique constraint rejects any duplicate created by a simultaneous request
    return {"saved": len(wanted)}


@router.get("/attendance")
def attendance_history(
    course_id: int, subject_id: int | None = None, date: date_type | None = None, student_id: int | None = None,
    db: Session = Depends(get_db), user: User = Depends(staff),
):
    assert_course_access(db, user, course_id)
    stmt = (
        select(Attendance).options(joinedload(Attendance.student), joinedload(Attendance.subject))
        .where(Attendance.course_id == course_id).order_by(Attendance.date.desc(), Attendance.student_id).limit(2000)
    )
    if subject_id:
        stmt = stmt.where(Attendance.subject_id == subject_id)
    if date:
        stmt = stmt.where(Attendance.date == date)
    if student_id:
        stmt = stmt.where(Attendance.student_id == student_id)
    return [
        {"id": a.id, "date": a.date, "status": a.status, "student_id": a.student_id,
         "student_code": a.student.student_code, "student_name": a.student.full_name,
         "subject_id": a.subject_id, "subject": a.subject.name}
        for a in db.scalars(stmt).unique()
    ]


@router.get("/attendance/summary")
def attendance_summary(course_id: int, subject_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(staff)):
    assert_course_access(db, user, course_id)
    stmt = (
        select(Student.id, Student.student_code, Student.full_name, func.count(Attendance.id), _present_sum())
        .join(Attendance, Attendance.student_id == Student.id).where(Attendance.course_id == course_id)
        .group_by(Student.id, Student.student_code, Student.full_name).order_by(Student.student_code)
    )
    if subject_id:
        stmt = stmt.where(Attendance.subject_id == subject_id)
    return [
        {"student_id": i, "student_code": c, "student_name": n, "total": t, "present": int(p or 0), "percentage": pct(p or 0, t)}
        for i, c, n, t, p in db.execute(stmt).all()
    ]


# ---------------- examinations ----------------
@router.post("/examinations", status_code=201)
def create_exam(p: ExamIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    assert_course_access(db, user, p.course_id)
    subject = db.get(Subject, p.subject_id)
    if subject is None or subject.course_id != p.course_id:
        raise HTTPException(400, "Subject does not belong to this course")
    e = Examination(**p.model_dump())
    db.add(e)
    commit(db)
    return {"id": e.id, "name": e.name, "course_id": e.course_id, "subject_id": e.subject_id, "max_marks": e.max_marks, "exam_date": e.exam_date}


@router.get("/examinations")
def list_exams(course_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    assert_course_access(db, user, course_id)
    stmt = select(Examination).options(joinedload(Examination.subject)).where(Examination.course_id == course_id).order_by(Examination.id.desc())
    return [
        {"id": e.id, "name": e.name, "subject_id": e.subject_id, "subject": e.subject.name, "max_marks": e.max_marks, "exam_date": e.exam_date}
        for e in db.scalars(stmt)
    ]


# ---------------- marks ----------------
def _exam_for_staff(db: Session, user: User, exam_id: int) -> Examination:
    exam = db.get(Examination, exam_id)
    if exam is None:
        raise HTTPException(404, "Examination not found")
    assert_course_access(db, user, exam.course_id)
    return exam


@router.get("/marks")
def exam_results(examination_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    exam = _exam_for_staff(db, user, examination_id)
    students = db.scalars(
        select(Student).join(Enrollment, Enrollment.student_id == Student.id)
        .where(Enrollment.course_id == exam.course_id).order_by(Student.student_code)
    ).all()
    marks = {m.student_id: m for m in db.scalars(select(Mark).where(Mark.examination_id == exam.id))}
    rows = []
    for s in students:
        m = marks.get(s.id)
        pc = pct(m.marks_obtained, exam.max_marks) if m else None
        rows.append({
            "student_id": s.id, "student_code": s.student_code, "student_name": s.full_name,
            "mark_id": m.id if m else None, "version": m.version if m else None,
            "marks_obtained": m.marks_obtained if m else None, "max_marks": exam.max_marks,
            "percentage": pc, "grade": grade_for(pc) if m else None,
        })
    return {"examination": {"id": exam.id, "name": exam.name, "max_marks": exam.max_marks}, "results": rows}


@router.post("/marks")
def save_marks(p: MarksBulkIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    exam = _exam_for_staff(db, user, p.examination_id)
    wanted = {e.student_id: e.marks_obtained for e in p.entries}
    if not set(wanted) <= _enrolled_ids(db, exam.course_id):
        raise HTTPException(400, "One or more students are not enrolled in this course")
    too_high = [sid for sid, v in wanted.items() if v > exam.max_marks]
    if too_high:
        raise HTTPException(400, f"Marks cannot exceed the maximum of {exam.max_marks:g}")
    existing = {m.student_id: m for m in db.scalars(select(Mark).where(Mark.examination_id == exam.id, Mark.student_id.in_(list(wanted))))}
    for sid, value in wanted.items():
        if sid in existing:
            existing[sid].marks_obtained, existing[sid].entered_by = value, _fac_id(user)
        else:
            db.add(Mark(student_id=sid, examination_id=exam.id, marks_obtained=value, entered_by=_fac_id(user)))
    commit(db)
    return {"saved": len(wanted)}


@router.put("/marks/{mark_id}")
def update_mark(mark_id: int, p: MarkUpdateIn, db: Session = Depends(get_db), user: User = Depends(staff)):
    m = db.get(Mark, mark_id)
    if m is None:
        raise HTTPException(404, "Mark not found")
    exam = _exam_for_staff(db, user, m.examination_id)
    if p.version != m.version:
        raise HTTPException(409, "These marks were changed by someone else. Reload and try again.")
    if p.marks_obtained > exam.max_marks:
        raise HTTPException(400, f"Marks cannot exceed the maximum of {exam.max_marks:g}")
    m.marks_obtained, m.entered_by = p.marks_obtained, _fac_id(user)
    commit(db)
    return {"id": m.id, "marks_obtained": m.marks_obtained, "version": m.version,
            "percentage": pct(m.marks_obtained, exam.max_marks), "grade": grade_for(pct(m.marks_obtained, exam.max_marks))}
