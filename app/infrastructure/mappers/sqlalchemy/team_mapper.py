from app.db.sqlalchemy.models.team import Team, TeamPermission
from app.domain.schemas.team.team import TeamCreate, TeamRead, TeamUpdate


class TeamMapper:
    @staticmethod
    def to_orm(team_create: TeamCreate) -> Team:
        """
        Map TeamCreate schema → ORM Team object.
        Also creates TeamPermission rows from allowed_purposes.
        """
        team = Team(
            name=team_create.name,
            description=team_create.description,
        )
        for purpose in team_create.allowed_purposes:
            team.permissions.append(TeamPermission(order_purpose=purpose))
        return team

    @staticmethod
    def to_read(team: Team) -> TeamRead:
        """
        Map ORM Team → TeamRead schema (includes permissions).
        """
        return TeamRead.model_validate(team)

    @staticmethod
    def update_orm(team: Team, team_update: TeamUpdate) -> Team:
        """
        Apply TeamUpdate schema → existing ORM Team object.
        """
        if team_update.name is not None:
            team.name = team_update.name
        if team_update.description is not None:
            team.description = team_update.description
        return team
