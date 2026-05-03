from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Quota, AuditLog
from app.schemas import (
    UserCreate,
    UserResponse,
    QuotaResponse,
    UserUpdate,
    PasswordUpdate,
    QuotaUpdate,
    AuditLogResponse,
)
from app.auth import require_privilege, hash_password, get_current_user, verify_password

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_privilege(100)),
) -> User:
    if user_in.privilege_level >= current_admin.privilege_level:
        raise HTTPException(
            status_code=403, detail="Cannot create user with equal or higher privileges"
        )

    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        privilege_level=user_in.privilege_level,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.add(Quota(user_id=new_user.id))
    db.commit()

    return new_user


@router.get("/", response_model=list[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_privilege(50)),
) -> list[User]:
    return db.query(User).offset(skip).limit(limit).all()


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me/password", status_code=204)
def update_password(
    passwords: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if not verify_password(passwords.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid old password")
    current_user.hashed_password = hash_password(passwords.new_password)
    db.commit()


@router.patch("/{user_id}", response_model=UserResponse)
def update_user_role(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_privilege(100)),
) -> User:
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_update.privilege_level >= current_admin.privilege_level:
        raise HTTPException(
            status_code=403, detail="Cannot set privilege equal or higher than yours"
        )
    target_user.privilege_level = user_update.privilege_level
    db.commit()
    db.refresh(target_user)
    return target_user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_privilege(100)),
) -> None:
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user or target_user.privilege_level >= current_admin.privilege_level:
        raise HTTPException(status_code=403, detail="Cannot delete this user")

    db.delete(target_user)
    db.commit()


@router.get("/{user_id}/quota", response_model=QuotaResponse)
def get_user_quota(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_privilege(50)),
) -> Quota:
    quota = db.query(Quota).filter(Quota.user_id == user_id).first()
    if not quota:
        raise HTTPException(status_code=404, detail="Quota not found")
    return quota


@router.patch("/{user_id}/quota", response_model=QuotaResponse)
def update_user_quota(
    user_id: int,
    quota_in: QuotaUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_privilege(100)),
) -> Quota:
    quota = db.query(Quota).filter(Quota.user_id == user_id).first()
    if not quota:
        raise HTTPException(status_code=404, detail="Quota not found")
    quota.max_tokens = quota_in.max_tokens
    db.commit()
    db.refresh(quota)
    return quota


@router.get("/{user_id}/logs", response_model=list[AuditLogResponse])
def get_user_logs(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AuditLog]:
    if current_user.id != user_id and current_user.privilege_level < 50:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
