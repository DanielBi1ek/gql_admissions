import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, ScalarResolver, createInputs2
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType

AdmissionGQLModel = typing.Annotated["AdmissionGQLModel", strawberry.lazy(".AdmissionGQLModel")]
StudyProgramGQLModel = typing.Annotated["StudyProgramGQLModel", strawberry.lazy(".StudyProgramGQLModel")]

@createInputs2
class EnrollmentInputFilter:
    id: IDType
    admission_id: IDType
    study_program_id: IDType
    status_id: IDType

@strawberry.federation.type(keys=["id"], description="Enrollment record for a student")
class EnrollmentGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).EnrollmentModel

    admission_id: typing.Optional[IDType] = strawberry.field(default=None, description="admission reference", permission_classes=[OnlyForAuthentized])
    study_program_id: typing.Optional[IDType] = strawberry.field(default=None, description="program enrolled", permission_classes=[OnlyForAuthentized])
    status_id: typing.Optional[IDType] = strawberry.field(default=None, description="enrollment state", permission_classes=[OnlyForAuthentized])

    admission: typing.Optional[AdmissionGQLModel] = strawberry.field(
        description="related admission",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver[AdmissionGQLModel](fkey_field_name="admission_id")
    )

@strawberry.type(description="Enrollment queries")
class EnrollmentQuery:
    enrollment_by_id: typing.Optional[EnrollmentGQLModel] = strawberry.field(
        description="get enrollment by id",
        permission_classes=[OnlyForAuthentized],
        resolver=EnrollmentGQLModel.load_with_loader
    )

    enrollment_page: typing.List[EnrollmentGQLModel] = strawberry.field(
        description="page of enrollments",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[EnrollmentGQLModel](whereType=EnrollmentInputFilter)
    )
