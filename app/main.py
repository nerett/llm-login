from fastapi import FastAPI
from app.database import engine, Base
from app.routers import users, auth_router, proxy

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LLM login proxy", version="0.1.0")

app.include_router(auth_router.router)
app.include_router(users.router)
app.include_router(proxy.router)
