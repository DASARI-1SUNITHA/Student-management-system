from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.database.session import get_db
from app.models import Course, Department, Subject
from app.schemas.schemas import CourseIn, SubjectIn
from app.services.common import commit

router = APIRouter(tags=["Courses & Subjects"])
admin_only = [Depends(require_roles("admin"))]


def course_out(c: Course) -> dict:
    return {"id": c.id, "name": c.name, "code": c.code, "credits": c.credits,
            "department_id": c.department_id, "department": c.department.name}


def subject_out(s: Subject) -> dict:
    return {"id": s.id, "name": s.name, "code": s.code, "course_id": s.course_id, "course": s.course.name}


# ---------- courses ----------
@router.get("/courses", dependencies=[Depends(get_current_user)])
def list_courses(department_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(Course).options(joinedload(Course.department)).order_by(Course.name)
    if department_id:
        stmt = stmt.where(Course.department_id == department_id)
    return [course_out(c) for c in db.scalars(stmt)]


@router.post("/courses", status_code=201, dependencies=admin_only)
def create_course(p: CourseIn, db: Session = Depends(get_db)):
    if db.get(Department, p.department_id) is None:
        raise HTTPException(404, "Department not found")
    c = Course(name=p.name.strip(), code=p.code.strip().upper(), credits=p.credits, department_id=p.department_id)
    db.add(c)
    commit(db)
    return course_out(db.get(Course, c.id))


@router.put("/courses/{course_id}", dependencies=admin_only)
def update_course(course_id: int, p: CourseIn, db: Session = Depends(get_db)):
    c = db.get(Course, course_id)
    if c is None:
        raise HTTPException(404, "Course not found")
    if db.get(Department, p.department_id) is None:
        raise HTTPException(404, "Department not found")
    c.name, c.code, c.credits, c.department_id = p.name.strip(), p.code.strip().upper(), p.credits, p.department_id
    commit(db)
    return course_out(db.get(Course, c.id))


@router.delete("/courses/{course_id}", status_code=204, dependencies=admin_only)
def delete_course(course_id: int, db: Session = Depends(get_db)):
    c = db.get(Course, course_id)
    if c is None:
        raise HTTPException(404, "Course not found")
    db.delete(c)
    commit(db)


# ---------- subjects ----------
@router.get("/subjects", dependencies=[Depends(get_current_user)])
def list_subjects(course_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(Subject).options(joinedload(Subject.course)).order_by(Subject.name)
    if course_id:
        stmt = stmt.where(Subject.course_id == course_id)
    return [subject_out(s) for s in db.scalars(stmt)]


@router.post("/subjects", status_code=201, dependencies=admin_only)
def create_subject(p: SubjectIn, db: Session = Depends(get_db)):
    if db.get(Course, p.course_id) is None:
        raise HTTPException(404, "Course not found")
    s = Subject(name=p.name.strip(), code=p.code.strip().upper(), course_id=p.course_id)
    db.add(s)
    commit(db)
    return subject_out(db.get(Subject, s.id))


@router.put("/subjects/{subject_id}", dependencies=admin_only)
def update_subject(subject_id: int, p: SubjectIn, db: Session = Depends(get_db)):
    s = db.get(Subject, subject_id)
    if s is None:
        raise HTTPException(404, "Subject not found")
    if db.get(Course, p.course_id) is None:
        raise HTTPException(404, "Course not found")
    s.name, s.code, s.course_id = p.name.strip(), p.code.strip().upper(), p.course_id
    commit(db)
    return subject_out(db.get(Subject, s.id))


@router.delete("/subjects/{subject_id}", status_code=204, dependencies=admin_only)
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    s = db.get(Subject, subject_id)
    if s is None:
        raise HTTPException(404, "Subject not found")
    db.delete(s)
    commit(db)
