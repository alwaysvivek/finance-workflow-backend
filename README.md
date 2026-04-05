# Multi-Tenant Financial Workflow Backend

[![Live Demo](https://img.shields.io/badge/Live_Demo-Render-brightgreen)](https://finance-workflow-backend.onrender.com/docs)

> [!NOTE]
> **Live Demo**: [https://finance-workflow-backend.onrender.com/docs](https://finance-workflow-backend.onrender.com/docs)
>
> *Please note: This is hosted on Render's free tier. The service automatically goes to sleep after 15 minutes of inactivity. The first request may take ~30 seconds to spin up.*

A production-grade, multi-tenant financial record backend built using FastAPI, SQLModel, and specialized multi-tier RBAC architecture.

## How to Run

1. **Environment Setup**
    Ensure Python 3.10+ is installed.
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2. **Launch the Server**
    ```bash
    uvicorn app.main:app --reload
    ```
    The Swagger UI will be available at `http://localhost:8000/docs`.

3. **Running the Tests**
    The app comes with an automated `pytest` suite simulating isolated DB conditions:
    ```bash
    PYTHONPATH=. pytest -v app/tests/
    ```

## API Endpoints

### Authentication
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api/v1/auth/register` | Public | Register a new user |
| POST | `/api/v1/auth/login` | Public | OAuth2 login, returns JWT token |
| GET | `/api/v1/users/me` | Authenticated | Get current user profile |

### Transactions
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api/v1/transactions/` | Admin, Analyst | Create a new transaction (status: Pending) |
| GET | `/api/v1/transactions/` | Authenticated | List transactions (supports `?type=`, `?category=`, `?status=`, `?skip=`, `?limit=`) |
| GET | `/api/v1/transactions/{id}` | Authenticated | Get a single transaction by ID |
| PUT | `/api/v1/transactions/{id}` | Admin, Analyst | Update a pending transaction's fields |
| PUT | `/api/v1/transactions/{id}/approve` | Admin | Approve a pending transaction (self-approval blocked) |
| PUT | `/api/v1/transactions/{id}/reject` | Admin | Reject a pending transaction |
| DELETE | `/api/v1/transactions/{id}` | Admin | Soft-delete a transaction |

### Analytics (Dashboard Summary)
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/v1/analytics/total-spend` | Admin, Analyst | Total approved expenses for the company |
| GET | `/api/v1/analytics/category-breakdown` | Admin, Analyst | Expense totals grouped by category |
| GET | `/api/v1/analytics/monthly-trend` | Admin, Analyst | Monthly expense trends |
| GET | `/api/v1/analytics/approval-rate` | Admin, Analyst | Count of approved/rejected/pending transactions |

## Architecture Decisions

The system is designed with a strict **layered architecture**:
- **API Routers (`app/api/v1/endpoints`)**: Kept intentionally "thin." Routes handle parameter parsing, HTTP exceptions, and delegating pure requests into business tasks.
- **Service Layer (`app/services/`)**: Centralized business logic. Functions like `TransactionService.approve_transaction()` wrap data changes and audit-log generations inside **atomic commits** (`db.commit()` / `db.rollback()`), guaranteeing data consistency.
- **Dependency Interfaces (`app/api/deps.py`)**: Abstracted request verifications. Auth decodes happen uniquely here.
- **Generic Responses**: Every API endpoint (apart from OAuth2 standard login) emits a standard, predictable data format enveloping JSON records: `{"data": {...}, "meta": {...}}`.

## Multi-Tenancy Explanation

The core mechanism for ensuring multiple companies cleanly interact with the service is a **Shared Database / Shared Schema approach**. To avoid a developer accidently querying leaked data:
1. Every relevant model inherits a `TenantMixin` which strictly forces a `company_id` Foreign Key constraint onto the rows.
2. Every Service/Query implicitly filters against the JWT session's `current_user.company_id`. Even fetching a single transaction via `db.get()` forces an implicit validation `tx.company_id == current_user.company_id`.

## RBAC Design

Role-Based Access Control assigns every User to one of three roles:
- `Viewer`: Read-only insights.
- `Analyst`: Creation and update privileges (Able to generate and modify `Pending` transactions).
- `Admin`: Full destructive and authorization privileges (Able to trigger Workflow actions like `Approve` or `Reject` and execute soft-deletes).

The `get_role_checker` FastAPI dependency dynamically prevents unpermitted network calls from even making it into the router scope.

## Assumptions & Business Rules

- **Self-approval prevention**: An admin cannot approve a transaction they created — a second admin must sign off. This mirrors real-world dual-control financial workflows.
- **Immutable after approval**: Once a transaction is `Approved` or `Rejected`, its fields can no longer be edited. Only `Pending` transactions are mutable.
- **Soft-delete**: Transactions are never physically removed from the database; a `deleted_at` timestamp is set, and all queries filter out soft-deleted records.
- **Audit logging**: Every create, update, approve, reject, and delete action generates an immutable `AuditLog` record for compliance traceability.

## Optional Enhancements Implemented

| Enhancement | Details |
|-------------|---------|
| JWT Authentication | Stateless token auth (HS256, 30-min expiry) via `python-jose` + `passlib/bcrypt` |
| Pagination | `skip`/`limit` query params on list endpoints |
| Soft Delete | `deleted_at` timestamp-based soft-delete |
| Unit Tests | `pytest` suite with in-memory SQLite, tests RBAC, tenant isolation, self-approval prevention |
| API Documentation | Auto-generated Swagger UI at `/docs` |
| Audit Trail | Immutable `AuditLog` table tracking all state changes |
| Multi-Tenancy | Row-level company isolation across all queries |
| Approval Workflow | Pending → Approved/Rejected state machine with dual-control |

## Tradeoffs: DB Layer
This framework ships locally leveraging `SQLite` bound natively via `SQLModel`, facilitating extremely quick local onboarding. 
- *Why SQLite*: Instant replication and mock testing (no Docker/Postgres daemon overhead).
- *Production Expectation*: The models, however, are fully configured using standard SQLAlchemy constraints (`String`, `Decimal`, explicit Foreign Keys) expecting **PostgreSQL**. In a live scenario, this must migrate to Postgres for concurrent atomic locks (important when multiple admins try to hit `/approve` simultaneously), specialized DATE_TRUNC implementations, and row-level security scaling.

