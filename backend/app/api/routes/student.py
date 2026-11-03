from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import current_student
from app.database.session import get_db
from app.models import Attendance, Course, Enrollment, Examination, Faculty, FacultyCourse, Mark, Student, Subject
from app.schemas.schemas import StudentSelfUpdate
from app.services.common import commit, grade_for, pct

# Every query below is filtered by the logged-in student's OWN id, taken from the token's user.
# There are no {student_id} URL parameters at all, so IDOR is impossible by design.
router = APIRouter(prefix="/student", tags=["Student"])


def _profile(s: Student) -> dict:
    return {
        "id": s.id, "student_code": s.student_code, "full_name": s.full_name, "email": s.user.email,
        "phone": s.phone, "gender": s.gender, "date_of_birth": s.date_of_birth, "address": s.address,
        "department": s.department.name, "course": s.course.name, "admission_date": s.admission_date, "status": s.status,
    }


def _attendance(db: Session, s: Student) -> dict:
    rows = db.scalars(
        select(Attendance).options(joinedload(Attendance.subject)).where(Attendance.student_id == s.id)
        .order_by(Attendance.date.desc())
    ).unique().all()
    per: dict = {}
    for a in rows:
        d = per.setdefault(a.subject.name, {"present": 0, "total": 0})
        d["total"] += 1
        d["present"] += a.status == "present"
    present = sum(d["present"] for d in per.values())
    return {
        "overall": {"present": present, "absent": len(rows) - present, "total": len(rows), "percentage": pct(present, len(rows))},
        "subject_wise": [{"subject": k, **v, "percentage": pct(v["present"], v["total"])} for k, v in sorted(per.items())],
        "records": [{"date": a.date, "subject": a.subject.name, "status": a.status} for a in rows],
    }


def _marks(db: Session, s: Student) -> dict:
    rows = db.execute(
        select(Mark, Examination, Subject, Course)
        .join(Examination, Examination.id == Mark.examination_id)
        .join(Subject, Subject.id == Examination.subject_id).join(Course, Course.id == Examination.course_id)
        .where(Mark.student_id == s.id).order_by(Examination.exam_date.desc().nulls_last(), Examination.id.desc())
    ).all()
    results = [
        {"exam": e.name, "subject": sub.name, "course": c.name, "exam_date": e.exam_date,
         "marks_obtained": m.marks_obtained, "max_marks": e.max_marks,
         "percentage": pct(m.marks_obtained, e.max_marks), "grade": grade_for(pct(m.marks_obtained, e.max_marks))}
        for m, e, sub, c in rows
    ]
    got, mx = sum(r["marks_obtained"] for r in results), sum(r["max_marks"] for r in results)
    return {"results": results, "summary": {"total_obtained": got, "total_max": mx, "percentage": pct(got, mx), "grade": grade_for(pct(got, mx)) if results else None}}


def _courses(db: Session, s: Student) -> list[dict]:
    courses = db.scalars(
        select(Course).options(joinedload(Course.department))
        .join(Enrollment, Enrollment.course_id == Course.id).where(Enrollment.student_id == s.id)
    ).all()
    out = []
    for c in courses:
        subjects = [x.name for x in db.scalars(select(Subject).where(Subject.course_id == c.id).order_by(Subject.name))]
        teachers = db.execute(
            select(Faculty).options(joinedload(Faculty.user))
            .join(FacultyCourse, FacultyCourse.faculty_id == Faculty.id).where(FacultyCourse.course_id == c.id)
        ).scalars().unique().all()
        out.append({
            "id": c.id, "name": c.name, "code": c.code, "department": c.department.name, "subjects": subjects,
            "faculty": [{"name": f.full_name, "email": f.user.email, "designation": f.designation} for f in teachers],
        })
    return out


@router.get("/profile")
def profile(s: Student = Depends(current_student)):
    return _profile(s)


@router.put("/profile")
def update_profile(p: StudentSelfUpdate, s: Student = Depends(current_student), db: Session = Depends(get_db)):
    for k, v in p.model_dump(exclude_unset=True).items():  # only phone & address are even accepted by the schema
        setattr(s, k, v)
    commit(db)
    return _profile(s)


@router.get("/attendance")
def my_attendance(s: Student = Depends(current_student), db: Session = Depends(get_db)):
    return _attendance(db, s)


@router.get("/marks")
def my_marks(s: Student = Depends(current_student), db: Session = Depends(get_db)):
    return _marks(db, s)


@router.get("/courses")
def my_courses(s: Student = Depends(current_student), db: Session = Depends(get_db)):
    return _courses(db, s)


@router.get("/dashboard")
def dashboard(s: Student = Depends(current_student), db: Session = Depends(get_db)):
    att, marks, courses = _attendance(db, s), _marks(db, s), _courses(db, s)
    return {
        "profile": _profile(s),
        "enrolled_courses": courses,
        "attendance": att["overall"],
        "marks_summary": marks["summary"],
        "recent_results": marks["results"][:5],
        "recent_attendance": att["records"][:5],
    }
