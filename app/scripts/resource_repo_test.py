import uuid
from typing import AsyncGenerator
import pytest
import pytest_asyncio

from app.db.sqlalchemy.dependencies import get_session
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.resource.enums.resource_state import ResourceState
from app.domain.schemas.resource.enums.resource_type import ResourceType
from app.domain.schemas.resource.enums.rt_locations import RtLocations
from app.domain.schemas.resource.resource import RtCreate, StationCreate, CrawlerRouteCreate, PandemicRouteCreate, \
    StationUpdate
from app.infrastructure.repositories.sqlalchemy.resource_repository import SQLAlchemyResourceRepository


# -------------------
# Fixtures
# -------------------
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
async def resource_repo(session):
    return SQLAlchemyResourceRepository(session)


# -------------------
# Tests
# -------------------
@pytest.mark.asyncio
async def test_create_rt(resource_repo):
    rt = await resource_repo.create(
        RtCreate(name=f"RT-{uuid.uuid4()}", resource_state=ResourceState.PRODUCTION, location=RtLocations.X)
    )
    assert rt.id is not None
    assert rt.resource_type == ResourceType.RT
    assert rt.location == RtLocations.X


@pytest.mark.asyncio
async def test_create_station(resource_repo):
    station = await resource_repo.create(
        StationCreate(name="Station-1", resource_state=ResourceState.NOT_USABLE, version="v1.0")
    )
    assert station.id is not None
    assert station.resource_type == ResourceType.STATION
    assert station.version == "v1.0"


@pytest.mark.asyncio
async def test_create_other_resources(resource_repo):
    crawler = await resource_repo.create(
        CrawlerRouteCreate(name="Crawler-1", resource_state=ResourceState.PRODUCTION)
    )
    pandemic = await resource_repo.create(
        PandemicRouteCreate(name="Pandemic-1", resource_state=ResourceState.NOT_USABLE)
    )
    assert crawler.resource_type == ResourceType.CRAWLER_ROUTE
    assert pandemic.resource_type == ResourceType.PANDEMIC_ROUTE


@pytest.mark.asyncio
async def test_get_resource(resource_repo):
    # rt = await resource_repo.create(
    #     RtCreate(name="RT-2", resource_state=ResourceState.PRODUCTION, location=RtLocations.Y)
    # )
    fetched = await resource_repo.get(37)
    assert fetched is not None
    assert fetched.id == 10
    assert fetched.name == "RT-2"


@pytest.mark.asyncio
async def test_list_resources(resource_repo):
    resources = await resource_repo.list()
    assert isinstance(resources, list)
    assert len(resources) > 0


@pytest.mark.asyncio
async def test_list_by_type(resource_repo):
    rts = await resource_repo.list_by_type(ResourceType.RT)
    assert all(r.resource_type == ResourceType.RT for r in rts)


@pytest.mark.asyncio
async def test_update_station(resource_repo):
    station = await resource_repo.create(
        StationCreate(name="Station-2", resource_state=ResourceState.DEVELOPMENT, version="v1.0")
    )
    updated = await resource_repo.update(
        station.id, StationUpdate(version="v2.0", name="Updated Station")
    )
    assert updated.version == "v2.0"
    assert updated.name == "Updated Station"


@pytest.mark.asyncio
async def test_delete_resource(resource_repo):
    rt = await resource_repo.create(
        RtCreate(name="RT-3", resource_state=ResourceState.PRODUCTION, location=RtLocations.X)
    )
    deleted = await resource_repo.delete(rt.id)
    assert deleted
    # confirm deletion
    fetched = await resource_repo.get(rt.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_get_supported_types(resource_repo):
    types = await resource_repo.get_supported_types()
    assert ResourceType.RT.value in types
    assert ResourceType.STATION.value in types