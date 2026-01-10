import typing
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel


@strawberry.federation.type(keys=["id"], description="Study program definition")
class StudyProgramGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).StudyProgramModel

    name: typing.Optional[str] = strawberry.field(
        default=None,
        description="study program name",
        permission_classes=[OnlyForAuthentized]
    )
