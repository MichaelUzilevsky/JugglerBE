# import asyncio
#
#
# async def main():
#     """
#     Main entry point for the application.
#     """
#     pass
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
import uvicorn

from src.api.app_factory import AppFactory

app = AppFactory.create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)