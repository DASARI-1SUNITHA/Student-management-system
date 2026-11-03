"""Create the first Admin account (and optionally demo data).

Usage (from the backend folder, venv active):
    python seed.py --email admin@example.com --password "StrongPass#123"
    python seed.py --email admin@example.com --password "StrongPass#123" --demo
"""
import argparse
from datetime import date

from sqlalchemy import select

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models import Course, Department, Enrollment, Faculty, FacultyCourse, Student, Subject, User


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--demo", action="store_true", help="also create a sample department, course, faculty and student")
    a = ap.parse_args()
    if len(a.password) < 8:
        raise SystemExit("Password must be at least 8 characters")

    db = SessionLocal()
    if db.scalar(select(User).where(User.email == a.email.lower())):
        print("Admin already exists - nothing to do.")
    else:
        db.add(User(email=a.email.lower(), password_hash=hash_password(a.password), role="admin"))
        db.commit()
        print(f"Admin created: {a.email}")

    if a.demo and not db.scalar(select(Department).where(Department.code == "CSE")):
        dept = Department(name="Computer Science", code="CSE")
        db.add(dept); db.flush()
        course = Course(name="B.Tech Computer Science", code="BTCSE", credits=4, department_id=dept.id)
        db.add(course); db.flush()
        subs = [Subject(name=n, code=c, course_id=course.id) for n, c in (("Data Structures", "CS201"), ("Databases", "CS202"))]
        db.add_all(subs)
        fu = User(email="faculty@example.com", password_hash=hash_password("Faculty#123"), role="faculty")
        fac = Faculty(user=fu, faculty_code="F001", full_name="Dr. Asha Rao", department_id=dept.id,
                      qualification="PhD", designation="Professor")
        db.add(fac); db.flush()
        db.add(FacultyCourse(faculty_id=fac.id, course_id=course.id))
        su = User(email="student@example.com", password_hash=hash_password("Student#123"), role="student")
        stu = Student(user=su, student_code="S1001", full_name="Ravi Kumar", phone="9876543210", gender="male",
                      department_id=dept.id, course_id=course.id, admission_date=date.today(), status="active")
        db.add(stu); db.flush()
        db.add(Enrollment(student_id=stu.id, course_id=course.id))
        db.commit()
        print("Demo data created:\n  faculty@example.com / Faculty#123\n  student@example.com / Student#123")


if __name__ == "__main__":
    main()
