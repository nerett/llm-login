from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Quota

def test_login_success(client: TestClient) -> None:
    response = client.post("/auth/login", data={"username": "admin", "password": "adminpass"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_fail(client: TestClient) -> None:
    response = client.post("/auth/login", data={"username": "admin", "password": "wrong"})
    assert response.status_code == 401

def test_create_user_success(client: TestClient, admin_token: str) -> None:
    payload = {"username": "testuser", "password": "123", "privilege_level": 1}
    response = client.post("/users/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_create_user_forbidden(client: TestClient, admin_token: str) -> None:
    payload = {"username": "testadmin", "password": "123", "privilege_level": 100}
    response = client.post("/users/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    assert response.status_code == 403

def test_create_duplicate_user(client: TestClient, admin_token: str) -> None:
    payload = {"username": "testuser", "password": "123", "privilege_level": 1}
    client.post("/users/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    response = client.post("/users/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    assert response.status_code == 400

def test_get_users(client: TestClient, admin_token: str) -> None:
    response = client.get("/users/", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_me(client: TestClient, admin_token: str) -> None:
    response = client.get("/users/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "admin"

def test_update_password_success(client: TestClient, admin_token: str) -> None:
    payload = {"old_password": "adminpass", "new_password": "newadminpass"}
    response = client.patch(
        "/users/me/password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload
    )
    assert response.status_code == 204

def test_update_password_fail(client: TestClient, admin_token: str) -> None:
    payload = {"old_password": "wrong", "new_password": "newadminpass"}
    response = client.patch(
        "/users/me/password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload
    )
    assert response.status_code == 400

def test_update_user_role_success(client: TestClient, admin_token: str) -> None:
    payload = {"username": "roleuser", "password": "123", "privilege_level": 1}
    create_res = client.post("/users/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    user_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"privilege_level": 50}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["privilege_level"] == 50

def test_update_user_role_forbidden(client: TestClient, admin_token: str) -> None:
    payload = {"username": "roleuser2", "password": "123", "privilege_level": 1}
    create_res = client.post("/users/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    user_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"privilege_level": 100}
    )
    assert patch_res.status_code == 403

def test_update_user_role_not_found(client: TestClient, admin_token: str) -> None:
    response = client.patch(
        "/users/999",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"privilege_level": 50}
    )
    assert response.status_code == 404

def test_get_user_quota(client: TestClient, admin_token: str) -> None:
    response = client.get("/users/1/quota", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert "max_tokens" in response.json()

def test_get_user_quota_not_found(client: TestClient, admin_token: str) -> None:
    response = client.get("/users/999/quota", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 404

def test_update_user_quota(client: TestClient, admin_token: str) -> None:
    patch_res = client.patch(
        "/users/1/quota",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"max_tokens": 50000}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["max_tokens"] == 50000

def test_update_user_quota_not_found(client: TestClient, admin_token: str) -> None:
    patch_res = client.patch(
        "/users/999/quota",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"max_tokens": 50000}
    )
    assert patch_res.status_code == 404

def test_delete_user(client: TestClient, admin_token: str) -> None:
    payload = {"username": "todelete", "password": "123", "privilege_level": 1}
    create_res = client.post("/users/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    user_id = create_res.json()["id"]

    del_res = client.delete(f"/users/{user_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_res.status_code == 204

def test_delete_user_forbidden(client: TestClient, admin_token: str) -> None:
    del_res = client.delete("/users/1", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_res.status_code == 403

def test_invalid_token(client: TestClient) -> None:
    response = client.get("/users/", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401

def test_admin_logs(client: TestClient, admin_token: str) -> None:
    response = client.get("/admin/logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_admin_stats(client: TestClient, admin_token: str) -> None:
    response = client.get("/admin/stats/usage", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert "total_requests" in response.json()

def test_user_logs(client: TestClient, admin_token: str) -> None:
    response = client.get("/users/1/logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_quota_forecast(client: TestClient, admin_token: str) -> None:
    response = client.get("/users/1/quota-forecast", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert "average_daily_tokens" in response.json()

def test_proxy_success(client: TestClient, admin_token: str) -> None:
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(status_code=200, content=b"mocked response")
        response = client.post(
            "/proxy/llm/api/generate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"prompt": "test"}
        )
        assert response.status_code == 200
        assert response.content == b"mocked response"

def test_proxy_warning_threshold(client: TestClient, db_session: Session, admin_token: str) -> None:
    quota = db_session.query(Quota).filter(Quota.user_id == 1).first()
    if quota:
        quota.used_tokens = int(quota.max_tokens * 0.95)
        db_session.commit()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(status_code=200, content=b"mocked response")
        response = client.post(
            "/proxy/llm/api/generate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"prompt": "test"}
        )
        assert response.status_code == 200

def test_proxy_quota_exceeded(client: TestClient, db_session: Session, admin_token: str) -> None:
    quota = db_session.query(Quota).filter(Quota.user_id == 1).first()
    if quota:
        quota.used_tokens = quota.max_tokens
        db_session.commit()

    response = client.post(
        "/proxy/llm/api/generate",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"prompt": "test"}
    )
    assert response.status_code == 429

def test_proxy_backend_unreachable(client: TestClient, admin_token: str) -> None:
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.RequestError("Unreachable", request=httpx.Request("POST", ""))
        response = client.post(
            "/proxy/llm/api/generate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"prompt": "test"}
        )
        assert response.status_code == 502
