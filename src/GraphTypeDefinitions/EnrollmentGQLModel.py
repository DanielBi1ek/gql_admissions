import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType

# Forward references
AdmissionApplicationGQLModel = typing.Annotated["AdmissionApplicationGQLModel", strawberry.lazy(".AdmissionApplicationGQLModel")]


@createInputs2
class EnrollmentInputFilter:
    id: IDType
    application_id: IDType
    study_program_id: IDType
    status_id: IDType
    enrolled_at: datetime.datetime


@strawberry.federation.type(keys=["id"], description="Enrollment derived from admission application")
class EnrollmentGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).EnrollmentModel

    application_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="admission application reference",
        permission_classes=[OnlyForAuthentized]
    )

    study_program_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="study program reference",
        permission_classes=[OnlyForAuthentized]
    )

    status_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="enrollment status id",
        permission_classes=[OnlyForAuthentized]
    )

    enrolled_at: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="enrollment date",
        permission_classes=[OnlyForAuthentized]
    )

    application: typing.Optional["AdmissionApplicationGQLModel"] = strawberry.field(
        description="related admission application",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["AdmissionApplicationGQLModel"](fkey_field_name="application_id")
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


from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating an enrollment")
class EnrollmentInsertGQLModel:
    application_id: IDType = strawberry.field(description="Admission application reference")
    study_program_id: IDType = strawberry.field(description="Study program reference")
    status_id: typing.Optional[IDType] = strawberry.field(default=None, description="Enrollment status")
    enrolled_at: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="Enrollment date")


@strawberry.input(description="Input model for updating an enrollment")
class EnrollmentUpdateGQLModel:
    id: IDType = strawberry.field(description="Enrollment id")
    lastchange: datetime.datetime = strawberry.field(description="Last change timestamp")
    study_program_id: typing.Optional[IDType] = None
    status_id: typing.Optional[IDType] = None
    enrolled_at: typing.Optional[datetime.datetime] = None


@strawberry.input(description="Input model for deleting an enrollment")
class EnrollmentDeleteGQLModel:
    id: IDType = strawberry.field(description="Enrollment id")
    lastchange: datetime.datetime = strawberry.field(description="Last change timestamp")


@strawberry.type(description="Enrollment mutations")
class EnrollmentMutation:
    @strawberry.mutation(
        description="Insert an enrollment record",
        permission_classes=[OnlyForAuthentized]
    )
    async def enrollment_insert(
            self,
            info: strawberry.Info,
            enrollment: EnrollmentInsertGQLModel
    ) -> typing.Union[EnrollmentGQLModel, InsertError[EnrollmentGQLModel]]:
        import uuid

        try:
            loader = getLoadersFromInfo(info).EnrollmentModel

            enrollment_data = {
                "id": uuid.uuid4(),
                "application_id": enrollment.application_id,
                "study_program_id": enrollment.study_program_id,
                "status_id": enrollment.status_id,
                "enrolled_at": enrollment.enrolled_at,
                "rbacobject_id": None,
                "createdby_id": uuid.UUID("66d8a57c-9ff3-40c3-a019-07808b5150a2"),
                "changedby_id": None,
            }

            from ..DBDefinitions.EnrollmentModel import EnrollmentModel
            db_row = EnrollmentModel(**enrollment_data)

            session = loader.session
            session.add(db_row)
            await session.commit()
            await session.refresh(db_row)

            return EnrollmentGQLModel.from_dataclass(db_row)

        except Exception as e:
            return InsertError[EnrollmentGQLModel](
                msg=str(e),
                _input=enrollment
            )

    @strawberry.mutation(
        description="Update an enrollment record",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[UpdateError, EnrollmentGQLModel]()]
    )
    async def enrollment_update(
            self,
            info: strawberry.Info,
            enrollment: EnrollmentUpdateGQLModel,
            db_row: typing.Any
    ) -> typing.Union[EnrollmentGQLModel, UpdateError[EnrollmentGQLModel]]:
        try:
            loader = getLoadersFromInfo(info).EnrollmentModel
            session = loader.session

            if enrollment.study_program_id is not None:
                db_row.study_program_id = enrollment.study_program_id
            if enrollment.status_id is not None:
                db_row.status_id = enrollment.status_id
            if enrollment.enrolled_at is not None:
                db_row.enrolled_at = enrollment.enrolled_at

            db_row.lastchange = datetime.datetime.now()

            session.add(db_row)
            await session.commit()
            await session.refresh(db_row)

            return EnrollmentGQLModel.from_dataclass(db_row)

        except Exception as e:
            return UpdateError[EnrollmentGQLModel](
                msg=str(e),
                _input=enrollment
            )

    @strawberry.mutation(
        description="Delete an enrollment record",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[DeleteError, EnrollmentGQLModel]()]
    )
    async def enrollment_delete(
            self,
            info: strawberry.Info,
            enrollment: EnrollmentDeleteGQLModel,
            db_row: typing.Any
    ) -> typing.Optional[DeleteError[EnrollmentGQLModel]]:
        try:
            loader = getLoadersFromInfo(info).EnrollmentModel
            session = loader.session

            await session.delete(db_row)
            await session.commit()

            return None

        except Exception as e:
            return DeleteError[EnrollmentGQLModel](
                msg=str(e),
                _input=enrollment
            )
