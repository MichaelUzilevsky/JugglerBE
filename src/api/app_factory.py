from contextlib import asynccontextmanager
from sys import prefix
from typing import cast, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import logger
from src.api.middleware.logging import log_requests
from src.api.v1.routes import users, resources
from src.db.mongodb.mongodb import MongoDBManager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    yield
    # Shutdown logic
    logger.info("Shutting Application Down")
    mongodb = MongoDBManager()
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

        return app
