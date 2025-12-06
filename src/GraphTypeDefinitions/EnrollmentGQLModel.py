import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, ScalarResolver, createInputs2, VectorResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType

AdmissionGQLModel = typing.Annotated["AdmissionGQLModel", strawberry.lazy(".AdmissionGQLModel")]
StudyProgramGQLModel = typing.Annotated["StudyProgramGQLModel", strawberry.lazy(".StudyProgramGQLModel")]
# forward reference to PaymentGQLModel and PaymentInputFilter
PaymentGQLModel = typing.Annotated["PaymentGQLModel", strawberry.lazy(".PaymentGQLModel")]
PaymentInputFilter = typing.Annotated["PaymentInputFilter", strawberry.lazy(".PaymentGQLModel")]

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

    payments: typing.List["PaymentGQLModel"] = strawberry.field(
        description="payments for this enrollment",
        permission_classes=[OnlyForAuthentized],
        resolver=VectorResolver["PaymentGQLModel"](fkey_field_name="enrollment_id", whereType=PaymentInputFilter)
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

# mutations
from uoishelpers.resolvers import InputModelMixin, InsertError, Insert, UpdateError, Update, DeleteError, Delete
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension
from uoishelpers.gqlpermissions.RbacProviderExtension import RbacProviderExtension
from uoishelpers.gqlpermissions.RbacInsertProviderExtension import RbacInsertProviderExtension
from uoishelpers.gqlpermissions.UserRoleProviderExtension import UserRoleProviderExtension
from uoishelpers.gqlpermissions.UserAccessControlExtension import UserAccessControlExtension

@strawberry.input(
    description="Input model for creating an enrollment"
)
class EnrollmentInsertGQLModel(InputModelMixin):
    getLoader = EnrollmentGQLModel.getLoader
    id: typing.Optional[IDType] = strawberry.field(default=None)
    admission_id: typing.Optional[IDType] = strawberry.field(default=None)
    study_program_id: typing.Optional[IDType] = strawberry.field(default=None)
    status_id: typing.Optional[IDType] = strawberry.field(default=None)

    createdby_id: strawberry.Private[IDType] = None

@strawberry.input(
    description="Input model for updating an enrollment"
)
class EnrollmentUpdateGQLModel:
    id: IDType = strawberry.field()
    lastchange: datetime.datetime = strawberry.field()
    admission_id: typing.Optional[IDType] = strawberry.field(default=None)
    study_program_id: typing.Optional[IDType] = strawberry.field(default=None)
    status_id: typing.Optional[IDType] = strawberry.field(default=None)
    changedby_id: strawberry.Private[IDType] = None

@strawberry.input(
    description="Input model for deleting an enrollment"
)
class EnrollmentDeleteGQLModel:
    id: IDType = strawberry.field()
    lastchange: datetime.datetime = strawberry.field()

@strawberry.type(description="Enrollment mutations")
class EnrollmentMutation:
    @strawberry.mutation(
        description="Insert an enrollment",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            UserAccessControlExtension[InsertError, EnrollmentGQLModel](roles=[]),
            UserRoleProviderExtension[InsertError, EnrollmentGQLModel](),
            RbacInsertProviderExtension[InsertError, EnrollmentGQLModel](),
            LoadDataExtension[InsertError, EnrollmentGQLModel](
                getLoader=EnrollmentGQLModel.getLoader,
                primary_key_name="admission_id"
            )
        ],
    )
    async def enrollment_insert(self, info: strawberry.Info, enrollment: EnrollmentInsertGQLModel, rbacobject_id: IDType, user_roles: typing.List[dict]) -> typing.Union[EnrollmentGQLModel, InsertError[EnrollmentGQLModel]]:
        return await Insert[EnrollmentGQLModel].DoItSafeWay(info=info, entity=enrollment)

    @strawberry.mutation(
        description="Update an enrollment",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            LoadDataExtension[UpdateError, EnrollmentGQLModel](),
            UserRoleProviderExtension[UpdateError, EnrollmentGQLModel](),
            RbacProviderExtension[UpdateError, EnrollmentGQLModel](),
            UserAccessControlExtension[UpdateError, EnrollmentGQLModel](roles=[]),
        ],
    )
    async def enrollment_update(self, info: strawberry.Info, enrollment: EnrollmentUpdateGQLModel) -> typing.Union[EnrollmentGQLModel, UpdateError[EnrollmentGQLModel]]:
        return await Update[EnrollmentGQLModel].DoItSafeWay(info=info, entity=enrollment)

    @strawberry.mutation(
        description="Delete an enrollment",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            LoadDataExtension[DeleteError, EnrollmentGQLModel](),
            UserRoleProviderExtension[DeleteError, EnrollmentGQLModel](),
            RbacProviderExtension[DeleteError, EnrollmentGQLModel](),
            UserAccessControlExtension[DeleteError, EnrollmentGQLModel](roles=[]),
        ],
    )
    async def enrollment_delete(self, info: strawberry.Info, enrollment: EnrollmentDeleteGQLModel) -> typing.Optional[DeleteError[EnrollmentGQLModel]]:
        return await Delete[EnrollmentGQLModel].DoItSafeWay(info=info, entity=enrollment)
