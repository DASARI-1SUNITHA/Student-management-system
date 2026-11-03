from datetime import date, datetime

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('admin','faculty','student')", name="ck_users_role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")
    faculty = relationship("Faculty", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    code: Mapped[str] = mapped_column(String(20), unique=True)
    credits: Mapped[int] = mapped_column(Integer, default=3)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)

    department = relationship("Department")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    code: Mapped[str] = mapped_column(String(20), unique=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)

    course = relationship("Course")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    full_name: Mapped[str] = mapped_column(String(150), index=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    gender: Mapped[str | None] = mapped_column(String(10))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    address: Mapped[str | None] = mapped_column(Text)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    admission_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active")

    user = relationship("User", back_populates="student")
    department = relationship("Department")
    course = relationship("Course")


class Faculty(Base):
    __tablename__ = "faculty"

    id: Mapped[int] = mapped_column(primary_key=True)
    faculty_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    full_name: Mapped[str] = mapped_column(String(150), index=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    qualification: Mapped[str | None] = mapped_column(String(150))
    designation: Mapped[str | None] = mapped_column(String(100))

    user = relationship("User", back_populates="faculty")
    department = relationship("Department")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_enrollment"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    enrolled_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FacultyCourse(Base):
    __tablename__ = "faculty_courses"
    __table_args__ = (UniqueConstraint("faculty_id", "course_id", name="uq_faculty_course"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", "date", name="uq_attendance_student_subject_date"),
        CheckConstraint("status IN ('present','absent')", name="ck_attendance_status"),
        Index("ix_attendance_course_date", "course_id", "date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculty.id", ondelete="SET NULL"))
    date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10))

    subject = relationship("Subject")
    student = relationship("Student")


class Examination(Base):
    __tablename__ = "examinations"
    __table_args__ = (CheckConstraint("max_marks > 0", name="ck_exam_max_marks"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), index=True)
    max_marks: Mapped[float] = mapped_column(Float)
    exam_date: Mapped[date | None] = mapped_column(Date)

    course = relationship("Course")
    subject = relationship("Subject")


class Mark(Base):
    __tablename__ = "marks"
    __table_args__ = (
        UniqueConstraint("student_id", "examination_id", name="uq_mark_student_exam"),
        CheckConstraint("marks_obtained >= 0", name="ck_marks_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    examination_id: Mapped[int] = mapped_column(ForeignKey("examinations.id", ondelete="CASCADE"), index=True)
    marks_obtained: Mapped[float] = mapped_column(Float)
    entered_by: Mapped[int | None] = mapped_column(ForeignKey("faculty.id", ondelete="SET NULL"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    version: Mapped[int] = mapped_column(Integer, default=1)  # optimistic locking

    student = relationship("Student")
    examination = relationship("Examination")

    __mapper_args__ = {"version_id_col": version}
