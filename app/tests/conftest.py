import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.db.session import get_session
from app.models.models import User, Company, RoleEnum
from app.core.security import get_password_hash, create_access_token

# Setup in-memory sqlite db for testing
sqlite_url = "sqlite://"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="setup_data")
def setup_data_fixture(session: Session):
    # Create two companies
    company1 = Company(name="Company Alpha")
    company2 = Company(name="Company Beta")
    session.add_all([company1, company2])
    session.commit()
    session.refresh(company1)
    session.refresh(company2)

    # Co1 Users
    admin1 = User(
        email="admin1@co1.com",
        hashed_password=get_password_hash("password123"),
        role=RoleEnum.ADMIN,
        company_id=company1.id
    )
    viewer1 = User(
        email="viewer1@co1.com",
        hashed_password=get_password_hash("password123"),
        role=RoleEnum.VIEWER,
        company_id=company1.id
    )
    
    # Co2 Users
    admin2 = User(
        email="admin2@co2.com",
        hashed_password=get_password_hash("password123"),
        role=RoleEnum.ADMIN,
        company_id=company2.id
    )
    
    session.add_all([admin1, viewer1, admin2])
    session.commit()
    session.refresh(admin1)
    session.refresh(viewer1)
    session.refresh(admin2)

    return {
        "co1": company1, "co2": company2,
        "admin1": admin1, "viewer1": viewer1, "admin2": admin2
    }

def get_token_headers(user: User):
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}
