import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType

@createInputs2
class AdmissionInputFilter:
    id: IDType
    applicant_name: str
    applicant_email: str
    status: str

@strawberry.federation.type(keys=["id"], description="Admission to the university (simple)")
class AdmissionGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).AdmissionModel

    applicant_name: typing.Optional[str] = strawberry.field(default=None, description="applicant full name", permission_classes=[OnlyForAuthentized])
    applicant_email: typing.Optional[str] = strawberry.field(default=None, description="applicant email", permission_classes=[OnlyForAuthentized])
    applied_date: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="date of application", permission_classes=[OnlyForAuthentized])
    status: typing.Optional[str] = strawberry.field(default=None, description="admission status", permission_classes=[OnlyForAuthentized])

@strawberry.type(description="Admission queries")
class AdmissionQuery:
    admission_by_id: typing.Optional[AdmissionGQLModel] = strawberry.field(
        description="get admission by id",
        permission_classes=[OnlyForAuthentized],
        resolver=AdmissionGQLModel.load_with_loader
    )

    admission_page: typing.List[AdmissionGQLModel] = strawberry.field(
        description="page of admissions",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[AdmissionGQLModel](whereType=AdmissionInputFilter)
    )
