import argparse
import os
from app.database import SessionLocal, engine, Base
from app.models import User, Quota
from app.auth import hash_password

Base.metadata.create_all(bind=engine)

def create_first_admin(password: str) -> None:
    with SessionLocal() as db:
        if db.query(User).filter(User.username == "admin").first():
            print("Admin already exists.")
            return

        admin = User(
            username="admin",
            hashed_password=hash_password(password),
            privilege_level=100
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        quota = Quota(user_id=admin.id, max_tokens=1000000, used_tokens=0)
        db.add(quota)
        db.commit()

        print(f"Super-admin 'admin' successfully created with ID: {admin.id}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Create initial admin user")
    parser.add_argument(
        "-p", "--password",
        type=str,
        help="Admin password"
    )
    args = parser.parse_args()

    password: str | None = args.password or os.environ.get("ADMIN_PASSWORD")

    if not password:
        print("Error: Password must be provided via --password or ADMIN_PASSWORD environment variable.")
        raise SystemExit(1)

    create_first_admin(password)

if __name__ == "__main__":
    main()
