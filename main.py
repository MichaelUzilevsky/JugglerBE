import asyncio
from datetime import datetime, timedelta
from tkinter.font import names

from pymongo import version

from src import config
from src.db.mongodb.mongo_crud import MongoCrud
from src.db.mongodb.mongodb import MongoDBManager
from src.exceptions.orders_exceptions.order_conflict_exception import OrderConflictException
from src.exceptions.orders_exceptions.permission_denied_exception import PermissionDeniedException
from src.handlers.orders_handler import OrdersHandler
from src.handlers.resources_handler import ResourcesHandler
from src.handlers.users_handler import UsersHandler
from src.models.orders.enums.order_purpose import OrderPurpose
from src.models.orders.order import Order
from src.models.resources.enums.resource_state import ResourceState
from src.models.resources.enums.resources_environmets import ResourceEnvironments
from src.models.resources.enums.rt_locations import RtLocations
from src.models.resources.rt import Rt
from src.models.resources.station import Station
from src.models.users.user import User
from src.models.users.user_login import UserLogin
from src.models.users.user_role import UserRole


async def main():
    """
    Main entry point for the application.
    """

    orders_mongo_curd = MongoCrud(Order, config.get_value("mongodb", "collections", "orders"))
    users_mongo_crud = MongoCrud(User, config.get_value("mongodb", "collections", "users"))
    resources_config_data = config.get_value("mongodb", "collections", "resources")

    users_handler = UsersHandler(users_mongo_crud)
    resource_handler = ResourcesHandler(resources_config_data)

    orders_handler = OrdersHandler(orders_mongo_curd, resource_handler, users_handler)

    # Create Users
    # admin_user = User(username="admin", password="admin", full_name="nigga", email="sss", role=UserRole.ADMIN)
    # normal_user = User(username="user", password="user", full_name="nigga", email="sss", role=UserRole.USER)
    #
    # admin_user = await users_handler.sign_up(admin_user)
    # normal_user = await users_handler.sign_up(normal_user)

    login_admin = UserLogin(username="admin", password="admin")
    login_user = UserLogin(username="user", password="user")

    admin_user = await users_handler.login(login_admin)
    normal_user = await users_handler.login(login_user)

    # Create Test Resources
    resource1 = Rt(name="RT1", location=RtLocations.X, resource_state=ResourceState.NOT_USABLE)
    resource2 = Rt(name="RT2", location=RtLocations.Y, resource_state=ResourceState.PRODUCTION)
    resource3 = Station(name="Station 1",
                        environment=ResourceEnvironments.ZNIF,
                        version="1.0.1",
                        resource_state=ResourceState.DEVELOPMENT)

    # resource1 = await resource_handler.create(Rt, resource1)
    # resource2 = await resource_handler.create(Rt, resource2)
    # resource3 = await resource_handler.create(Station, resource3)


    # Create a valid order
    start = datetime.now() + timedelta(hours=1)
    end = start + timedelta(hours=2)


    # order1 = Order(
    #     user_id=normal_user.id,
    #     resources_ids=[resource1.id],
    #     purpose=OrderPurpose.TEST,
    #     start_time=start,
    #     end_time=end,
    # )
    #
    # created_order = await orders_handler.create_order(order1)
    #
    # order2 = Order(
    #     user_id=normal_user.id,
    #     resources_ids=[resource1.id],
    #     purpose=OrderPurpose.TEST,
    #     start_time=start + timedelta(minutes=30),
    #     end_time=end + timedelta(hours=1),
    # )
    # await orders_handler.create_order(order2)

    # Approve order with non-admin → should raise PermissionDeniedException
    # try:
    #     await orders_handler.approve_order("687225bcfd8bd38808519d46", normal_user.id)
    # except PermissionDeniedException as e:
    #     print(f"Expected permission error: {e}")

    # Approve order with admin
    # await orders_handler.approve_order("687225bcfd8bd38808519d46", admin_user.id)

    # created_order = await orders_handler.get_order("687225bcfd8bd38808519d46")
    # # Try updating approved order → no validation
    # await orders_handler.approve_order(created_order.id, admin_user.id)

    # Create new order that overlaps → should now raise conflict because of approved order
    try:
        overlap_order = Order(
            user_id=normal_user.id,
            resources_ids=["687225bcfd8bd38808519d43"],
            purpose=OrderPurpose.TEST,
            start_time=datetime.fromisoformat("2025-07-12T13:07:08.470+00:00"),
            end_time=datetime.fromisoformat("2025-07-12T15:07:08.470+00:00"),
        )
        await orders_handler.create_order(overlap_order)
    except OrderConflictException as e:
        print(f"Expected conflict after approval: {e}")

    # # Move order to pend
    # await orders_handler.move_order_to_pending(created_order.id, admin_user.id)
    #
    # # Reject order
    # await orders_handler.reject_order(created_order.id, admin_user.id)
    #
    # # Delete order
    # await orders_handler.delete_order(created_order.id)
    #
    # # Get all orders and validate clean-up
    # remaining_orders = await orders_handler.get_all()
    # print(f"Remaining orders count: {len(remaining_orders)}")
    #
    # # Get orders by resource class
    # orders_by_class = await orders_handler.get_orders_by_resource_class(Rt)
    # print(f"Orders by resource type: {len(orders_by_class)}")


if __name__ == "__main__":
    asyncio.run(main())
