import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.session import get_db
from app.models import Faculty, FacultyCourse, Student, User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)
) -> User:
    """Identify the caller from the JWT, then load the user (and role) FROM THE DATABASE."""
    if creds is None:
        raise HTTPException(401, "Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    try:
        user_id = int(decode_token(creds.credentials)["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(401, "Account not found or deactivated")
    return user


def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "You do not have permission to perform this action")
        return user

    return checker


def current_student(user: User = Depends(require_roles("student"))) -> Student:
    if user.student is None:
        raise HTTPException(404, "Student profile not found")
    return user.student


def current_faculty(user: User = Depends(require_roles("faculty"))) -> Faculty:
    if user.faculty is None:
        raise HTTPException(404, "Faculty profile not found")
    return user.faculty


def accessible_course_ids(db: Session, user: User) -> list[int] | None:
    """None = unrestricted (admin). Faculty get only their assigned course ids."""
    if user.role == "admin":
        return None
    if user.faculty is None:
        return []
    return list(db.scalars(select(FacultyCourse.course_id).where(FacultyCourse.faculty_id == user.faculty.id)))


def assert_course_access(db: Session, user: User, course_id: int) -> None:
    ids = accessible_course_ids(db, user)
    if ids is not None and course_id not in ids:
        raise HTTPException(403, "This course is not assigned to you")
