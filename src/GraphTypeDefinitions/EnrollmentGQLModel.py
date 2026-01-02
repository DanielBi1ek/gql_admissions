import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, VectorResolver, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType

# Forward references
AdmissionGQLModel = typing.Annotated["AdmissionGQLModel", strawberry.lazy(".AdmissionGQLModel")]
PaymentGQLModel = typing.Annotated["PaymentGQLModel", strawberry.lazy(".PaymentGQLModel")]
PaymentInputFilter = typing.Annotated["PaymentInputFilter", strawberry.lazy(".PaymentGQLModel")]


@createInputs2
class EnrollmentInputFilter:
    id: IDType
    admission_id: IDType
    study_program_id: IDType
    #status_id: IDType
    payment: float


@strawberry.federation.type(keys=["id"], description="Student enrollment in a study program")
class EnrollmentGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).EnrollmentModel

    admission_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="admission reference",
        permission_classes=[OnlyForAuthentized]
    )

    study_program_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="study program reference",
        permission_classes=[OnlyForAuthentized]
    )



    payment: typing.Optional[float] = strawberry.field(
        default=None,
        description="enrollment payment amount",
        permission_classes=[OnlyForAuthentized]
    )

    # Relationships
    admission: typing.Optional["AdmissionGQLModel"] = strawberry.field(
        description="related admission",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["AdmissionGQLModel"](fkey_field_name="admission_id")
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


# Mutations
from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating an enrollment")
class EnrollmentInsertGQLModel:
    admission_id: IDType = strawberry.field(description="Admission reference")
    study_program_id: IDType = strawberry.field(description="Study program reference")
    #status_id: IDType = strawberry.field(description="Enrollment status")
    payment: typing.Optional[float] = strawberry.field(default=0.0, description="Payment amount")


@strawberry.input(description="Input model for updating an enrollment")
class EnrollmentUpdateGQLModel:
    id: IDType = strawberry.field(description="Enrollment id")
    lastchange: datetime.datetime = strawberry.field(description="Last change timestamp")
    study_program_id: typing.Optional[IDType] = None
   # status_id: typing.Optional[IDType] = None
    payment: typing.Optional[float] = None


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

        print("=" * 80)
        print("DEBUG: enrollment_insert CALLED!!!")
        print(f"DEBUG: admission_id: {enrollment.admission_id}")
        print(f"DEBUG: study_program_id: {enrollment.study_program_id}")
        #print(f"DEBUG: status_id: {enrollment.status_id}")
        print(f"DEBUG: payment: {enrollment.payment}")
        print("=" * 80)

        loader = getLoadersFromInfo(info).EnrollmentModel

        try:
            enrollment_data = {
                "id": uuid.uuid4(),
                "admission_id": enrollment.admission_id,
                "study_program_id": enrollment.study_program_id,
                #"status_id": enrollment.status_id,
                "payment": enrollment.payment,
                "rbacobject_id": None,
                "createdby_id": uuid.UUID("66d8a57c-9ff3-40c3-a019-07808b5150a2"),
                "changedby_id": None,
            }

            print(f"DEBUG: Creating enrollment with data: {enrollment_data}")

            from ..DBDefinitions.EnrollmentModel import EnrollmentModel
            db_row = EnrollmentModel(**enrollment_data)

            session = loader.session
            session.add(db_row)
            await session.commit()
            await session.refresh(db_row)

            print(f"DEBUG: Insert successful! ID: {db_row.id}")

            return EnrollmentGQLModel.from_dataclass(db_row)

        except Exception as e:
            print(f"DEBUG: Exception during insert: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

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
        print("=" * 80)
        print("DEBUG: enrollment_update CALLED!!!")
        print(f"DEBUG: id: {enrollment.id}")
        print("=" * 80)

        try:
            loader = getLoadersFromInfo(info).EnrollmentModel
            session = loader.session

            if enrollment.study_program_id is not None:
                db_row.study_program_id = enrollment.study_program_id
            #if enrollment.status_id is not None:
             #   db_row.status_id = enrollment.status_id
            if enrollment.payment is not None:
                db_row.payment = enrollment.payment

            import datetime
            db_row.lastchange = datetime.datetime.now()

            session.add(db_row)
            await session.commit()
            await session.refresh(db_row)

            print(f"DEBUG: Update successful!")

            return EnrollmentGQLModel.from_dataclass(db_row)

        except Exception as e:
            print(f"DEBUG: Exception during update: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

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
        print("=" * 80)
        print("DEBUG: enrollment_delete CALLED!!!")
        print(f"DEBUG: id: {enrollment.id}")
        print("=" * 80)

        try:
            loader = getLoadersFromInfo(info).EnrollmentModel
            session = loader.session

            await session.delete(db_row)
            await session.commit()

            print(f"DEBUG: Delete successful!")

            return None

        except Exception as e:
            print(f"DEBUG: Exception during delete: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

            return DeleteError[EnrollmentGQLModel](
                msg=str(e),
                _input=enrollment
            )