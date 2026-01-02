import typing
import datetime
import strawberry
import os
import json
import uuid

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, VectorResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import getUserFromInfo
from .BaseGQLModel import BaseGQLModel, IDType

# forward reference to EnrollmentGQLModel and EnrollmentInputFilter
EnrollmentGQLModel = typing.Annotated["EnrollmentGQLModel", strawberry.lazy(".EnrollmentGQLModel")]
EnrollmentInputFilter = typing.Annotated["EnrollmentInputFilter", strawberry.lazy(".EnrollmentGQLModel")]


@createInputs2
class AdmissionInputFilter:
    id: IDType
    applicant_name: str
    applicant_email: str
    # status_id: IDType


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
    # status_id: typing.Optional[IDType] = strawberry.field(default=None, description="admission status_id",permission_classes=[OnlyForAuthentized])

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
    # status_id: typing.Optional[IDType] = "pending"


@strawberry.input(description="Input model for updating an admission")
class AdmissionUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    applicant_name: typing.Optional[str] = None
    applicant_email: typing.Optional[str] = None
    # status_id: typing.Optional[IDType] = None


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
        from uoishelpers.resolvers import Insert

        # Get authenticated user
        user = getUserFromInfo(info=info)
        createdby_id = user["id"]

        # Set the createdby_id on the input
        admission.createdby_id = createdby_id
        admission.rbacobject_id = None

        print("=" * 80)
        print("DEBUG: admission_insert CALLED!!!")
        print(f"DEBUG: User ID: {createdby_id}")
        print(f"DEBUG: applicant_name: {admission.applicant_name}")
        print("=" * 80)

        return await Insert[AdmissionGQLModel].DoItSafeWay(info=info, entity=admission)

    @strawberry.mutation(
        description="Update an admission record",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[UpdateError, AdmissionGQLModel]()]
    )
    async def admission_update(
            self,
            info: strawberry.Info,
            admission: AdmissionUpdateGQLModel,
            db_row: typing.Any
    ) -> typing.Union[AdmissionGQLModel, UpdateError[AdmissionGQLModel]]:
        from uoishelpers.resolvers import Update

        # Get authenticated user
        user = getUserFromInfo(info=info)
        user_id = user["id"]
        print(*"=" * 80)
        print("DEBUG: admission_update PERMISSION CHECK!!!")
        print(user_id)
        print(db_row.createdby_id)

        # Permission check: only creator can update
        if str(db_row.createdby_id) != user_id:
            return UpdateError[AdmissionGQLModel](
                _entity=db_row,
                msg="You are not allowed to update this admission",
                code="ae30e32b-94ec-4d59-9c1e-7eca3b75701e",
                location="admission_update",
                _input=admission
            )

        # Only update fields that are not None
        # Keep existing values for None fields
        if admission.applicant_name is None:
            admission.applicant_name = db_row.applicant_name
        if admission.applicant_email is None:
            admission.applicant_email = db_row.applicant_email

        # Set the changedby_id
        admission.changedby_id = user_id

        print("=" * 80)
        print("DEBUG: admission_update CALLED!!!")
        print(f"DEBUG: User ID: {user_id}")
        print(f"DEBUG: Admission ID: {admission.id}")
        print("=" * 80)

        return await Update[AdmissionGQLModel].DoItSafeWay(info=info, entity=admission)

    @strawberry.mutation(
        description="Delete an admission record",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[DeleteError, AdmissionGQLModel]()]
    )
    async def admission_delete(
            self,
            info: strawberry.Info,
            admission: AdmissionDeleteGQLModel,
            db_row: typing.Any
    ) -> typing.Optional[DeleteError[AdmissionGQLModel]]:
        from uoishelpers.resolvers import Delete

        # Get authenticated user (for logging)
        user = getUserFromInfo(info=info)
        user_id = user["id"]



        print("=" * 80)
        print("DEBUG: admission_delete CALLED!!!")
        print(f"DEBUG: User ID: {user_id}")
        print(f"DEBUG: Admission ID: {admission.id}")
        print("=" * 80)

        return await Delete[AdmissionGQLModel].DoItSafeWay(info=info, entity=admission)