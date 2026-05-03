import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Quota, AuditLog
from app.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/proxy", tags=["proxy"])

def estimate_tokens(payload: bytes) -> int:
    text = payload.decode(errors="ignore")
    return max(1, len(text.split()) // 2)

def send_quota_warning(username: str) -> None:
    """ For now it's print-only. May be impelented in the future. """
    print(f"NOTIFICATION EMAIL: User {username} has reached 90% of their token quota.")

@router.post("/llm/{path:path}")
async def proxy_llm(
    path: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    quota = db.query(Quota).filter(Quota.user_id == current_user.id).first()
    if not quota:
        raise HTTPException(status_code=403, detail="Quota not assigned")

    body = await request.body()
    estimated_cost = estimate_tokens(body)

    if quota.used_tokens + estimated_cost > quota.max_tokens:
        raise HTTPException(status_code=429, detail="Quota exceeded")

    if (quota.used_tokens + estimated_cost) > (quota.max_tokens * 0.9):
        background_tasks.add_task(send_quota_warning, current_user.username)

    target_url = f"{settings.llm_backend_url}/{path}"

    async with httpx.AsyncClient() as client:
        try:
            llm_response = await client.post(
                target_url,
                content=body,
                headers={"Content-Type": "application/json"},
                timeout=60.0
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail="LLM Backend is unreachable") from exc

    quota.used_tokens += estimated_cost
    audit_log = AuditLog(
        user_id=current_user.id,
        endpoint=f"/llm/{path}",
        tokens_estimated=estimated_cost
    )
    db.add(audit_log)
    db.commit()

    return Response(
        content=llm_response.content,
        status_code=llm_response.status_code,
        media_type=llm_response.headers.get("content-type")
    )
