from contextlib import asynccontextmanager
from typing import cast, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import logger
from app.api.exceptions.handlers import domain_exception_handler, unhandled_exception_handler
from app.api.middleware.logging import log_requests
from app.api.v1.routes import users, resources, orders, metadata, health, auth
from app.db.sqlalchemy.manager import SQLAlchemyManager
from app.domain.exceptions.domain_exception import DomainException


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("Starting Application...")

    # Initialize manager
    app.state.db_manager = SQLAlchemyManager()

    if await app.state.db_manager.check_connection():
        logger.info("Database connection is healthy")
    else:
        logger.critical("Database connection failed")

    yield

    # Cleanup
    await app.state.db_manager.close()

    logger.info("Shutting Application Down...")


class AppFactory:
    @staticmethod
    def create_app() -> FastAPI:
        app = FastAPI(title="JugglerAPI", version="1.0.0", lifespan=lifespan)

        # Add Middleware
        app.middleware("http")(log_requests)

        app.add_middleware(
            cast("_MiddlewareFactory", CORSMiddleware),
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Register global exception handlers
        app.add_exception_handler(DomainException, domain_exception_handler)
        app.add_exception_handler(Exception, unhandled_exception_handler)

        # Include versioned routes
        app.include_router(auth.router, prefix="/api/v1")
        app.include_router(users.router, prefix="/api/v1")
        app.include_router(resources.router, prefix="/api/v1")
        app.include_router(orders.router, prefix="/api/v1")
        app.include_router(metadata.router, prefix="/api/v1")
        app.include_router(health.router, prefix="/api/v1")

        return app
