import logging

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

log = logging.getLogger("sms")


def grade_for(percentage: float) -> str:
    for limit, g in ((90, "A+"), (80, "A"), (70, "B+"), (60, "B"), (50, "C"), (40, "D")):
        if percentage >= limit:
            return g
    return "F"


def pct(part: float, whole: float) -> float:
    return round(part * 100.0 / whole, 2) if whole else 0.0


def commit(db: Session) -> None:
    """Commit and translate database constraint errors into clean HTTP errors."""
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        log.warning("Integrity error: %s", exc.orig)
        raise HTTPException(
            409,
            "Conflict: duplicate value, or this record is still linked to other records.",
        )
    except StaleDataError:
        db.rollback()
        raise HTTPException(409, "Someone else changed this record at the same time. Reload and retry.")


def paginate(db: Session, stmt, page: int, page_size: int):
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = db.scalars(stmt.limit(page_size).offset((page - 1) * page_size)).unique().all()
    return total, items
