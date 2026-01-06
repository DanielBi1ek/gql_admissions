import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType


@createInputs2
class StudyProgramInputFilter:
    id: IDType
    name: str
    name_en: str
    code: str
    description: str
    degree_level: str
    duration_years: int
    credits: int


@strawberry.federation.type(keys=["id"], description="Study program catalog entry")
class StudyProgramGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).StudyProgramModel

    name: typing.Optional[str] = strawberry.field(default=None, description="study program name", permission_classes=[OnlyForAuthentized])
    name_en: typing.Optional[str] = strawberry.field(default=None, description="study program name (English)", permission_classes=[OnlyForAuthentized])
    code: typing.Optional[str] = strawberry.field(default=None, description="study program code", permission_classes=[OnlyForAuthentized])
    description: typing.Optional[str] = strawberry.field(default=None, description="study program description", permission_classes=[OnlyForAuthentized])
    degree_level: typing.Optional[str] = strawberry.field(default=None, description="degree level", permission_classes=[OnlyForAuthentized])
    duration_years: typing.Optional[int] = strawberry.field(default=None, description="program duration in years", permission_classes=[OnlyForAuthentized])
    credits: typing.Optional[int] = strawberry.field(default=None, description="total credits", permission_classes=[OnlyForAuthentized])


@strawberry.type(description="Study program queries")
class StudyProgramQuery:
    study_program_by_id: typing.Optional[StudyProgramGQLModel] = strawberry.field(
        description="get study program by id",
        permission_classes=[OnlyForAuthentized],
        resolver=StudyProgramGQLModel.load_with_loader
    )

    study_program_page: typing.List[StudyProgramGQLModel] = strawberry.field(
        description="page of study programs",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[StudyProgramGQLModel](whereType=StudyProgramInputFilter)
    )


from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating a study program")
class StudyProgramInsertGQLModel:
    name: typing.Optional[str] = None
    name_en: typing.Optional[str] = None
    code: typing.Optional[str] = None
    description: typing.Optional[str] = None
    degree_level: typing.Optional[str] = None
    duration_years: typing.Optional[int] = None
    credits: typing.Optional[int] = None


@strawberry.input(description="Input model for updating a study program")
class StudyProgramUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    name: typing.Optional[str] = None
    name_en: typing.Optional[str] = None
    code: typing.Optional[str] = None
    description: typing.Optional[str] = None
    degree_level: typing.Optional[str] = None
    duration_years: typing.Optional[int] = None
    credits: typing.Optional[int] = None


@strawberry.input(description="Input model for deleting a study program")
class StudyProgramDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


@strawberry.type(description="Study program mutations")
class StudyProgramMutation:
    @strawberry.mutation(description="Insert a study program", permission_classes=[OnlyForAuthentized])
    async def study_program_insert(
        self,
        info: strawberry.Info,
        program: StudyProgramInsertGQLModel
    ) -> typing.Union[StudyProgramGQLModel, InsertError[StudyProgramGQLModel]]:
        from uoishelpers.resolvers import Insert

        return await Insert[StudyProgramGQLModel].DoItSafeWay(info=info, entity=program)

    @strawberry.mutation(
        description="Update a study program",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[UpdateError, StudyProgramGQLModel]()]
    )
    async def study_program_update(
        self,
        info: strawberry.Info,
        program: StudyProgramUpdateGQLModel,
        db_row: typing.Any
    ) -> typing.Union[StudyProgramGQLModel, UpdateError[StudyProgramGQLModel]]:
        from uoishelpers.resolvers import Update

        return await Update[StudyProgramGQLModel].DoItSafeWay(info=info, entity=program)

    @strawberry.mutation(
        description="Delete a study program",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[DeleteError, StudyProgramGQLModel]()]
    )
    async def study_program_delete(
        self,
        info: strawberry.Info,
        program: StudyProgramDeleteGQLModel,
        db_row: typing.Any
    ) -> typing.Optional[DeleteError[StudyProgramGQLModel]]:
        from uoishelpers.resolvers import Delete

        return await Delete[StudyProgramGQLModel].DoItSafeWay(info=info, entity=program)
