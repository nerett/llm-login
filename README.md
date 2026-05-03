# LLM Login Proxy

A secure, high-performance Reverse Proxy built with FastAPI for authenticating, logging, and limiting access to unauthenticated local LLM backends (like Ollama or vLLM).

## Features & Business Logic
- **JWT Authentication:** Secure user sessions using JWT and bcrypt password hashing.
- **Role-Based Access Control (RBAC):** Hierarchical privilege levels (users, managers, super-admins).
- **Token Quotas & Billing:** Calculates request weight (simulated token counting) and deducts from user quotas.
- **Asynchronous Notifications:** Utilizes FastAPI `BackgroundTasks` to send warnings when users reach 90% of their limits.
- **Audit Logging:** Every successful proxy request is logged into a relational database.
- **Aggregated Analytics:** Provides system-wide statistics via complex SQL aggregations (total usage, active users).
- **Transparent Reverse Proxying:** Forwards headers and JSON payloads transparently to the LLM backend using asynchronous `httpx`.

## Architecture
- **Framework:** FastAPI (Python 3.12+)
- **Database:** SQLite with SQLAlchemy (ORM)
- **Validation:** Pydantic V2
- **Environment Management:** `uv` package manager + `pydantic-settings`

## Installation and Setup

1. Install `uv` (if not installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the repository and install dependencies:
   ```bash
   uv sync
   ```

3. Configure environment variables in a `.env` file at the project root:
   ```env
   SECRET_KEY="your_super_secret_key"
   ADMIN_PASSWORD="secure_admin_password"
   LLM_BACKEND_URL="http://localhost:11434"
   ```

4. Initialize the database and create the first admin user:
   ```bash
   uv run python create_admin.py
   ```

5. Run the application:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

## Development & Testing
- **API Documentation:** Available at `http://127.0.0.1:8000/docs`
- **Run Tests (with Coverage):** `uv run pytest --cov=app tests/`
- **Lint Code:** `uv run pylint app/ tests/` (Target: 10.0/10.0)

## Author Information
Проект выполнил Андрей Цедрик (М01-507а) в рамках курса "Python для решения прикладных задач" на Цифровой кафедре МФТИ. Цель проекта заключается в разработке REST сервиса на основе `FastAPI` для управления доступом и распределением квоты использования при проксировании запросов к развернутым локально большим языковым моделям.
