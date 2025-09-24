# tests/test_order_repository.py
from typing import AsyncGenerator, List
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.sqlalchemy.dependencies import get_session
from app.domain.schemas.order.order import OrderCreate, OrderUpdate
from app.domain.schemas.resource.resource import RtCreate
from app.domain.schemas.user.user import UserCreate
from app.domain.schemas.order.order import  ResourceRead
from app.domain.schemas.order.enums.order_status import OrderStatus
from app.domain.schemas.order.enums.order_purpose import OrderPurpose
from app.infrastructure.repositories.sqlalchemy.order_repository import SQLAlchemyOrderRepository
from app.infrastructure.repositories.sqlalchemy.user_repository import SQLAlchemyUserRepository
from app.infrastructure.repositories.sqlalchemy.resource_repository import SQLAlchemyResourceRepository
from app.domain.schemas.resource.enums.resource_state import ResourceState
from app.domain.schemas.resource.enums.rt_locations import RtLocations
from app.domain.schemas.user.enums.user_role import UserRole


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    gen = get_session()
    session = await gen.__anext__()
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


@pytest_asyncio.fixture
async def resource_repo(session):
    return SQLAlchemyResourceRepository(session)


@pytest_asyncio.fixture
async def order_repo(session):
    return SQLAlchemyOrderRepository(session)


@pytest_asyncio.fixture
async def test_user(user_repo):
    user = await user_repo.create(UserCreate(
        username="orderuser",
        password="password",
        full_name="Order User",
        email="orderuser@example.com",
        role=UserRole.USER,
    ))
    return user


@pytest_asyncio.fixture
async def test_resources(resource_repo):
    resources: List[ResourceRead] = []
    for i in range(3):
        rt = await resource_repo.create(RtCreate(
            name=f"RT-{i}x",
            resource_state=ResourceState.PRODUCTION,
            location=RtLocations.X,
        ))
        resources.append(rt)
    return resources


@pytest.mark.asyncio
async def test_create_order(order_repo, test_user, test_resources):
    order_create = OrderCreate(
        user_id=test_user.id,
        purpose=OrderPurpose.TEST,
        status=OrderStatus.CREATED,
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(hours=1),
        resource_ids=[r.id for r in test_resources]
    )
    order = await order_repo.create(order_create)
    assert order.id is not None
    assert len(order.resources) == len(test_resources)
    assert order.user.id == test_user.id
    assert order.status_history == []


@pytest.mark.asyncio
async def test_get_order(order_repo,):
    # order_create = OrderCreate(
    #     user_id=test_user.id,
    #     purpose=OrderPurpose.TEST,
    #     status=OrderStatus.CREATED,
    #     start_time=datetime.utcnow(),
    #     end_time=datetime.utcnow() + timedelta(hours=1),
    #     resource_ids=[r.id for r in test_resources]
    # )
    # created_order = await order_repo.create(order_create)

    id = 6
    fetched_order = await order_repo.get(id)
    assert fetched_order is not None
    assert fetched_order.id == id
    assert len(fetched_order.resources) == 3
    assert fetched_order.user.id == 13


@pytest.mark.asyncio
async def test_list_orders(order_repo):
    orders = await order_repo.list()
    assert isinstance(orders, list)
    assert len(orders) > 0


@pytest.mark.asyncio
async def test_update_order(order_repo):
    order_create = OrderUpdate(
        user_id=21,
        purpose=OrderPurpose.MAINTENANCE,
        status=OrderStatus.PENDING,
        start_time=datetime.now()+ timedelta(hours=11),
        end_time=datetime.now() + timedelta(hours=15),
    )

    updated_order = await order_repo.update(8, order_create)
    assert updated_order.purpose == OrderPurpose.MAINTENANCE
    assert len(updated_order.resources) == 3


@pytest.mark.asyncio
async def test_delete_order(order_repo):
    # order_create = OrderCreate(
    #     user_id=test_user.id,
    #     purpose=OrderPurpose.TEST,
    #     status=OrderStatus.CREATED,
    #     start_time=datetime.utcnow(),
    #     end_time=datetime.utcnow() + timedelta(hours=1),
    #     resource_ids=[r.id for r in test_resources]
    # )
    # order = await order_repo.create(order_create)
    deleted = await order_repo.delete(6)
    assert deleted
    deleted_order = await order_repo.get(6)
    assert deleted_order is None


@pytest.mark.asyncio
async def test_get_orders_in_time_range(order_repo):
    start = datetime.now()
    end = start + timedelta(hours=2)
    # order_create = OrderCreate(
    #     user_id=test_user.id,
    #     purpose=OrderPurpose.TEST,
    #     status=OrderStatus.CREATED,
    #     start_time=start,
    #     end_time=end,
    #     resource_ids=[r.id for r in test_resources]
    # )
    # created_order = await order_repo.create(order_create)
    orders = await order_repo.get_orders_in_time_range(start - timedelta(minutes=5), end + timedelta(minutes=5))
    assert any(o.id ==7 for o in orders)


@pytest.mark.asyncio
async def test_get_users_orders(order_repo):
    # order_create = OrderCreate(
    #     user_id=test_user.id,
    #     purpose=OrderPurpose.TEST,
    #     status=OrderStatus.CREATED,
    #     start_time=datetime.utcnow(),
    #     end_time=datetime.utcnow() + timedelta(hours=1),
    #     resource_ids=[r.id for r in test_resources]
    # )
    # created_order = await order_repo.create(order_create)
    user_orders = await order_repo.get_users_orders(21)
    assert any(o.id == 7 for o in user_orders)
