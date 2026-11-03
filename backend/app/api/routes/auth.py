from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database.session import get_db
from app.models import User
from app.schemas.schemas import LoginIn, PasswordChangeIn
from app.services.common import commit, log

router = APIRouter(prefix="/auth", tags=["Auth"])


def user_info(u: User) -> dict:
    name, code = "Administrator", None
    if u.role == "student" and u.student:
        name, code = u.student.full_name, u.student.student_code
    elif u.role == "faculty" and u.faculty:
        name, code = u.faculty.full_name, u.faculty.faculty_code
    return {"id": u.id, "email": u.email, "role": u.role, "name": name, "code": code, "is_active": u.is_active}


@router.post("/login")
def login(p: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == p.email.lower()))
    # same message for every failure so attackers cannot discover which emails exist
    bad = HTTPException(401, "Invalid email or password")
    if user is None or not verify_password(p.password, user.password_hash):
        log.warning("Failed login for %s", p.email)
        raise bad
    if not user.is_active:
        raise HTTPException(403, "Your account is deactivated. Contact the administrator.")
    if p.role and p.role != user.role:  # wrong portal (role is still decided by the DB)
        raise HTTPException(401, f"These credentials are not for the {p.role} login")
    log.info("Login: %s (%s)", user.email, user.role)
    return {"access_token": create_access_token(user.id), "token_type": "bearer", "user": user_info(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_info(user)


@router.post("/change-password")
def change_password(p: PasswordChangeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(p.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")
    if p.current_password == p.new_password:
        raise HTTPException(400, "New password must differ from the current one")
    user.password_hash = hash_password(p.new_password)
    commit(db)
    return {"message": "Password changed successfully"}
