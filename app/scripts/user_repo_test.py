from typing import AsyncGenerator

import pytest

from app.db.sqlalchemy.dependencies import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.schemas.user.user import UserCreate, UserUpdate
from app.domain.schemas.user.enums.user_role import UserRole
from app.infrastructure.repositories.sqlalchemy.user_repository import SQLAlchemyUserRepository

# Sample test data
TEST_USER_1 = UserCreate(
    username="testuser1",
    password="password123",
    full_name="Test User 1",
    email="testuser1@example.com",
    role=UserRole.USER,
)

TEST_USER_2 = UserCreate(
    username="testuser2",
    password="password456",
    full_name="Test User 2",
    email="testuser2@example.com",
    role=UserRole.ADMIN,
)

import pytest_asyncio

@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    # create async generator instance
    gen = get_session()
    session = await gen.__anext__()  # get the first yielded session
    try:
        yield session
    finally:
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

@pytest_asyncio.fixture
async def user_repo(session):
    return SQLAlchemyUserRepository(session)



@pytest.mark.asyncio
async def test_create_user(user_repo):
    user = await user_repo.create(TEST_USER_1)
    assert user.id is not None
    assert user.username == TEST_USER_1.username
    assert user.email == TEST_USER_1.email


@pytest.mark.asyncio
async def test_get_user(user_repo):
    created_user = await user_repo.create(TEST_USER_2)
    fetched_user = await user_repo.get(created_user.id)
    assert fetched_user is not None
    assert fetched_user.id == created_user.id
    assert fetched_user.username == created_user.username


@pytest.mark.asyncio
async def test_list_users(user_repo):
    users = await user_repo.list()
    assert isinstance(users, list)
    assert len(users) > 0


@pytest.mark.asyncio
async def test_get_by_username(user_repo):
    user = await user_repo.get_by_username("testuser1")
    assert user is not None
    assert user.username == "testuser1"


@pytest.mark.asyncio
async def test_update_user(user_repo):
    user = await user_repo.get_by_username("testuser1")
    update_data = UserUpdate(full_name="Updated Test User 1", email="updated1@example.com")
    updated_user = await user_repo.update(user.id, update_data)
    assert updated_user.full_name == "Updated Test User 1"
    assert updated_user.email == "updated1@example.com"


@pytest.mark.asyncio
async def test_delete_user(user_repo):
    user = await user_repo.get_by_username("testuser1")
    deleted = await user_repo.delete(user.id)
    assert deleted
    # confirm deletion
    deleted_user = await user_repo.get(user.id)
    assert deleted_user is None
