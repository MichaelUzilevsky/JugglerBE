import uvicorn

from app.api.app_factory import AppFactory

app = AppFactory.create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000) # , access_log=False, log_level="warning"
