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
            team_id=user_create.team_id,
        )

    @staticmethod
    def to_read(user: User) -> UserRead:
        """
        Map ORM User → UserRead schema
        """
        return UserRead(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            team_id=user.team_id,
            team_name=user.team.name if user.team else None,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

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
        if user_update.team_id is not None:
            user.team_id = user_update.team_id

        return user
