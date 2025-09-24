from datetime import datetime

from app.db.sqlalchemy.models import User
from app.infrastructure.mappers.sqlalchemy.user_mapper import UserMapper
from app.domain.schemas.user.user import UserCreate, UserRead, UserUpdate
from app.domain.schemas.user.enums.user_role import UserRole


def test_to_orm():
    user_create = UserCreate(
        username="john_doe",
        password="hashed_password",
        full_name="John Doe",
        email="john@example.com",
        role=UserRole.USER,
    )

    user = UserMapper.to_orm(user_create)

    assert isinstance(user, User)
    assert user.username == "john_doe"
    assert user.password == "hashed_password"
    assert user.full_name == "John Doe"
    assert user.email == "john@example.com"
    assert user.role == UserRole.USER


def test_to_read():
    user = User(
        id=1,
        username="jane_doe",
        password="hashed_password",
        full_name="Jane Doe",
        email="jane@example.com",
        role=UserRole.ADMIN,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 2, 12, 0, 0),
    )

    user_read = UserMapper.to_read(user)

    assert isinstance(user_read, UserRead)
    assert user_read.id == 1
    assert user_read.username == "jane_doe"
    assert user_read.full_name == "Jane Doe"
    assert user_read.email == "jane@example.com"
    assert user_read.role == UserRole.ADMIN
    assert user_read.created_at == datetime(2024, 1, 1, 12, 0, 0)
    assert user_read.updated_at == datetime(2024, 1, 2, 12, 0, 0)


def test_update_orm():
    # Existing ORM object
    user = User(
        id=2,
        username="old_user",
        password="old_pass",
        full_name="Old Name",
        email="old@example.com",
        role=UserRole.USER,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    user_update = UserUpdate(
        username="new_user",
        full_name="New Name",
        email="new@example.com",
    )

    updated_user = UserMapper.update_orm(user, user_update)

    assert updated_user.username == "new_user"
    assert updated_user.full_name == "New Name"
    assert updated_user.email == "new@example.com"
    assert updated_user.password == "old_pass"  # unchanged
    assert updated_user.role == UserRole.USER   # unchanged
