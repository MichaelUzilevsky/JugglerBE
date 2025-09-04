from app.db.sqlalchemy.models import User
from app.domain.schemas.user.user import UserCreate, UserRead, UserUpdate


class UserMapper:
    @staticmethod
    def to_orm(user_create: UserCreate) -> User:
        """
        Map UserCreate schema → ORM User object
        """
        return User(
            username=user_create.username,
            password=user_create.password,
            full_name=user_create.full_name,
            email=user_create.email,
            role=user_create.role,
        )

    @staticmethod
    def to_read(user: User) -> UserRead:
        """
        Map ORM User → UserRead schema
        """
        return UserRead.model_validate(user)

    @staticmethod
    def update_orm(user: User, user_update: UserUpdate) -> User:
        """
        Apply UserUpdate schema → existing ORM User object
        """
        if user_update.username is not None:
            user.username = user_update.username
        if user_update.password is not None:
            user.password = user_update.password
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.email is not None:
            user.email = user_update.email
        if user_update.role is not None:
            user.role = user_update.role

        return user
