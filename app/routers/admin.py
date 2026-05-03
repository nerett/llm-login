from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, AuditLog
from app.schemas import AuditLogResponse, SystemStats
from app.auth import require_privilege

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/logs", response_model=list[AuditLogResponse])
def get_all_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_privilege(50))
) -> list[AuditLog]:
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

@router.get("/stats/usage", response_model=SystemStats)
def get_system_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_privilege(100))
) -> dict[str, int]:
    total_requests = db.query(AuditLog).count()
    total_tokens = db.query(func.sum(AuditLog.tokens_estimated)).scalar() or 0
    unique_users = db.query(AuditLog.user_id).distinct().count()

    return {
        "total_requests": total_requests,
        "total_tokens_used": total_tokens,
        "unique_active_users": unique_users
    }
