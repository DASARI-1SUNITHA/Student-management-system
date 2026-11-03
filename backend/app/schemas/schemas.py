from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

Phone = Field(default=None, pattern=r"^\+?[0-9]{7,15}$", description="7-15 digits, optional leading +")
Gender = Literal["male", "female", "other"]
StudentStatus = Literal["active", "inactive", "graduated", "suspended"]


# ---------- auth ----------
class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    role: Literal["admin", "faculty", "student"] | None = None  # which login portal was used


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


# ---------- academics ----------
class DepartmentIn(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=1, max_length=20)


class CourseIn(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=1, max_length=20)
    credits: int = Field(default=3, ge=1, le=30)
    department_id: int


class SubjectIn(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=1, max_length=20)
    course_id: int


class EnrollIn(BaseModel):
    student_id: int
    course_id: int


class AssignCoursesIn(BaseModel):
    course_ids: list[int]


# ---------- students / faculty ----------
class StudentCreate(BaseModel):
    student_code: str = Field(min_length=1, max_length=30)
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Phone
    gender: Gender | None = None
    date_of_birth: date | None = None
    address: str | None = Field(default=None, max_length=500)
    department_id: int
    course_id: int
    admission_date: date | None = None
    status: StudentStatus = "active"


class StudentUpdate(BaseModel):
    student_code: str | None = Field(default=None, min_length=1, max_length=30)
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Phone
    gender: Gender | None = None
    date_of_birth: date | None = None
    address: str | None = Field(default=None, max_length=500)
    department_id: int | None = None
    course_id: int | None = None
    admission_date: date | None = None
    status: StudentStatus | None = None
    is_active: bool | None = None


class StudentSelfUpdate(BaseModel):
    phone: str | None = Phone
    address: str | None = Field(default=None, max_length=500)


class FacultyCreate(BaseModel):
    faculty_code: str = Field(min_length=1, max_length=30)
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Phone
    department_id: int
    qualification: str | None = Field(default=None, max_length=150)
    designation: str | None = Field(default=None, max_length=100)
    course_ids: list[int] = []


class FacultyUpdate(BaseModel):
    faculty_code: str | None = Field(default=None, min_length=1, max_length=30)
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Phone
    department_id: int | None = None
    qualification: str | None = Field(default=None, max_length=150)
    designation: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


# ---------- attendance / marks ----------
class AttendanceRecord(BaseModel):
    student_id: int
    status: Literal["present", "absent"]


class AttendanceIn(BaseModel):
    course_id: int
    subject_id: int
    date: date
    records: list[AttendanceRecord] = Field(min_length=1)


class ExamIn(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    course_id: int
    subject_id: int
    max_marks: float = Field(gt=0, le=1000)
    exam_date: date | None = None


class MarkEntry(BaseModel):
    student_id: int
    marks_obtained: float = Field(ge=0)


class MarksBulkIn(BaseModel):
    examination_id: int
    entries: list[MarkEntry] = Field(min_length=1)


class MarkUpdateIn(BaseModel):
    marks_obtained: float = Field(ge=0)
    version: int  # the version the client last saw (concurrency check)
