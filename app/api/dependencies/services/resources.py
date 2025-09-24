from fastapi import Depends

from app.api.dependencies.repositories.resources import get_resource_repo
from app.domain.repositories.iresource_repository import IResourceRepository
from app.domain.services.resource_service import ResourceService


async def get_resource_service(resource_repo: IResourceRepository = Depends(get_resource_repo)) -> ResourceService:
    return ResourceService(resource_repo)
