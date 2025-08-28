from contextlib import asynccontextmanager
from typing import cast, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import logger
from src.api.middleware.logging import log_requests
from src.api.v1.routes import users, resources, orders, metadata
from src.db.mongodb.mongodb import MongoDBManager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("Starting Application...")
    mongodb = MongoDBManager()

    yield

    logger.info("Shutting Application Down...")
    await mongodb.close()


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

        # Include versioned routes
        app.include_router(users.router, prefix="/api/v1")
        app.include_router(resources.router, prefix="/api/v1")
        app.include_router(orders.router, prefix="/api/v1")
        app.include_router(metadata.router, prefix="/api/v1")

        return app
