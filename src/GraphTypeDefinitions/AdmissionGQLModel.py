import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, VectorResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType

# forward reference to EnrollmentGQLModel and EnrollmentInputFilter
EnrollmentGQLModel = typing.Annotated["EnrollmentGQLModel", strawberry.lazy(".EnrollmentGQLModel")]
EnrollmentInputFilter = typing.Annotated["EnrollmentInputFilter", strawberry.lazy(".EnrollmentGQLModel")]


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

    applicant_name: typing.Optional[str] = strawberry.field(default=None, description="applicant full name",
                                                            permission_classes=[OnlyForAuthentized])
    applicant_email: typing.Optional[str] = strawberry.field(default=None, description="applicant email",
                                                             permission_classes=[OnlyForAuthentized])
    applied_date: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="date of application",
                                                                        permission_classes=[OnlyForAuthentized])
    status: typing.Optional[str] = strawberry.field(default=None, description="admission status",
                                                    permission_classes=[OnlyForAuthentized])

    # related enrollments
    enrollment_records: typing.List["EnrollmentGQLModel"] = strawberry.field(
        description="enrollments created from this admission",
        permission_classes=[OnlyForAuthentized],
        resolver=VectorResolver["EnrollmentGQLModel"](fkey_field_name="admission_id", whereType=EnrollmentInputFilter)
    )


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


# mutations
from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating an admission")
class AdmissionInsertGQLModel:
    applicant_name: typing.Optional[str] = None
    applicant_email: typing.Optional[str] = None
    status: typing.Optional[str] = "pending"


@strawberry.input(description="Input model for updating an admission")
class AdmissionUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    applicant_name: typing.Optional[str] = None
    applicant_email: typing.Optional[str] = None
    status: typing.Optional[str] = None


@strawberry.input(description="Input model for deleting an admission")
class AdmissionDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


@strawberry.type(description="Admission mutations")
class AdmissionMutation:
    @strawberry.mutation(
        description="Insert an admission record",
        permission_classes=[OnlyForAuthentized]
    )
    async def admission_insert(
            self,
            info: strawberry.Info,
            admission: AdmissionInsertGQLModel
    ) -> typing.Union[AdmissionGQLModel, InsertError[AdmissionGQLModel]]:
        import uuid

        print("=" * 80)
        print("DEBUG: admission_insert CALLED!!!")
        print(f"DEBUG: applicant_name: {admission.applicant_name}")
        print(f"DEBUG: applicant_email: {admission.applicant_email}")
        print(f"DEBUG: status: {admission.status}")
        print("=" * 80)

        # Get loader and create the admission directly
        loader = getLoadersFromInfo(info).AdmissionModel

        try:
            # Create the admission data
            admission_data = {
                "id": uuid.uuid4(),
                "applicant_name": admission.applicant_name,
                "applicant_email": admission.applicant_email,
                "status": admission.status,
                "rbacobject_id": None,
                "createdby_id": uuid.UUID("66d8a57c-9ff3-40c3-a019-07808b5150a2"),
                "changedby_id": None,
            }

            print(f"DEBUG: Creating admission with data: {admission_data}")

            # Insert into database
            from ..DBDefinitions.AdmissionModel import AdmissionModel
            db_row = AdmissionModel(**admission_data)

            session = loader.session
            session.add(db_row)
            await session.commit()
            await session.refresh(db_row)

            print(f"DEBUG: Insert successful! ID: {db_row.id}")

            # Return the GQL model
            return AdmissionGQLModel.from_dataclass(db_row)

        except Exception as e:
            print(f"DEBUG: Exception during insert: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

            return InsertError[AdmissionGQLModel](
                msg=str(e),
                _input=admission
            )

    @strawberry.mutation(
        description="Update an admission record",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[UpdateError, AdmissionGQLModel]()]
    )
    async def admission_update(
            self,
            info: strawberry.Info,
            admission: AdmissionUpdateGQLModel
    ) -> typing.Union[AdmissionGQLModel, UpdateError[AdmissionGQLModel]]:
        from uoishelpers.resolvers import Update
        return await Update[AdmissionGQLModel].DoItSafeWay(info=info, entity=admission)

    @strawberry.mutation(
        description="Delete an admission record",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[DeleteError, AdmissionGQLModel]()]
    )
    async def admission_delete(
            self,
            info: strawberry.Info,
            admission: AdmissionDeleteGQLModel
    ) -> typing.Optional[DeleteError[AdmissionGQLModel]]:
        from uoishelpers.resolvers import Delete
        return await Delete[AdmissionGQLModel].DoItSafeWay(info=info, entity=admission)