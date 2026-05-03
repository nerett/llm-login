from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Quota
from app.schemas import UserCreate, UserResponse, QuotaResponse
from app.auth import require_privilege, hash_password

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_privilege(100))
) -> User:
    if user_in.privilege_level >= current_admin.privilege_level:
        raise HTTPException(status_code=403, detail="Cannot create user with equal or higher privileges")

    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        privilege_level=user_in.privilege_level
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    new_quota = Quota(user_id=new_user.id)
    db.add(new_quota)
    db.commit()

    return new_user

@router.get("/", response_model=list[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_privilege(50))
) -> list[User]:
    return db.query(User).offset(skip).limit(limit).all()

@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_privilege(100))
) -> None:
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.privilege_level >= current_admin.privilege_level:
        raise HTTPException(status_code=403, detail="Cannot delete this user")

    db.delete(target_user)
    db.commit()

@router.get("/{user_id}/quota", response_model=QuotaResponse)
def get_user_quota(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_privilege(50))
) -> Quota:
    quota = db.query(Quota).filter(Quota.user_id == user_id).first()
    if not quota:
        raise HTTPException(status_code=404, detail="Quota not found")
    return quota
