from sys import prefix
from typing import cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.logging import log_requests
from src.api.v1 import users


class AppFactory:
    @staticmethod
    def create_app() -> FastAPI:
        app = FastAPI(title="JugglerAPI", version="1.0.0")

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

        return app
