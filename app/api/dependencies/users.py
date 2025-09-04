from src import config
from src.db.cruds.mongo_crud import MongoCrud
from src.handlers.users_handler import UsersHandler
from src.models.users.user import User


def get_users_handler() -> UsersHandler:
    mongo_crud = MongoCrud(User, config.get_value("managers", "collections", "users"))
    user_handler = UsersHandler(mongo_crud)
    return user_handler
