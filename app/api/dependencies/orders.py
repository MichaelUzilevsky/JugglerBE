from src import config
from src.api.dependencies.resources import get_resources_handler
from src.api.dependencies.users import get_users_handler
from src.db.cruds.mongo_crud import MongoCrud
from src.handlers.orders_handler import OrdersHandler
from src.handlers.resources_handler import ResourcesHandler
from src.handlers.users_handler import UsersHandler
from src.models.orders.order import Order


def get_orders_handler() -> OrdersHandler:
    users_handler: UsersHandler = get_users_handler()
    resources_handler: ResourcesHandler = get_resources_handler()

    orders_crud = MongoCrud(Order, config.get_value("managers", "collections", "orders"))

    orders_handler: OrdersHandler = OrdersHandler(orders_crud, resources_handler, users_handler)

    return orders_handler
