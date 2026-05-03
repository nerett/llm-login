from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker, Session
from app.main import app
from app.database import Base, get_db
from app.models import User, Quota
from app.auth import hash_password

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TESTING_SESSION_LOCAL = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function", name="db_session")
def fixture_db_session() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    db = TESTING_SESSION_LOCAL()

    admin = User(
        username="admin",
        hashed_password=hash_password("adminpass"),
        privilege_level=100
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    quota = Quota(user_id=admin.id, max_tokens=10000, used_tokens=0)
    db.add(quota)
    db.commit()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function", name="client")
def fixture_client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function", name="admin_token")
def fixture_admin_token(client: TestClient) -> str:
    response = client.post("/auth/login", data={"username": "admin", "password": "adminpass"})
    return response.json()["access_token"]
