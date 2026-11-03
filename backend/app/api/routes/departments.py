from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database.session import get_db
from app.models import Department
from app.schemas.schemas import DepartmentIn
from app.services.common import commit

router = APIRouter(prefix="/departments", tags=["Departments"])


def out(d: Department) -> dict:
    return {"id": d.id, "name": d.name, "code": d.code}


@router.get("", dependencies=[Depends(get_current_user)])
def list_departments(db: Session = Depends(get_db)):
    return [out(d) for d in db.scalars(select(Department).order_by(Department.name))]


@router.post("", status_code=201, dependencies=[Depends(require_roles("admin"))])
def create_department(p: DepartmentIn, db: Session = Depends(get_db)):
    d = Department(name=p.name.strip(), code=p.code.strip().upper())
    db.add(d)
    commit(db)
    return out(d)


@router.put("/{dept_id}", dependencies=[Depends(require_roles("admin"))])
def update_department(dept_id: int, p: DepartmentIn, db: Session = Depends(get_db)):
    d = db.get(Department, dept_id)
    if d is None:
        raise HTTPException(404, "Department not found")
    d.name, d.code = p.name.strip(), p.code.strip().upper()
    commit(db)
    return out(d)


@router.delete("/{dept_id}", status_code=204, dependencies=[Depends(require_roles("admin"))])
def delete_department(dept_id: int, db: Session = Depends(get_db)):
    d = db.get(Department, dept_id)
    if d is None:
        raise HTTPException(404, "Department not found")
    db.delete(d)
    commit(db)  # fails with 409 if courses/students/faculty still use it
