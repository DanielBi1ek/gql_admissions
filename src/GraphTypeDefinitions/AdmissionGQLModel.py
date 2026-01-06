import typing
import datetime
import strawberry
import os
import json
import uuid

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, VectorResolver, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import getUserFromInfo
from .BaseGQLModel import BaseGQLModel, IDType

# forward reference to EnrollmentGQLModel and EnrollmentInputFilter
EnrollmentGQLModel = typing.Annotated["EnrollmentGQLModel", strawberry.lazy(".EnrollmentGQLModel")]
EnrollmentInputFilter = typing.Annotated["EnrollmentInputFilter", strawberry.lazy(".EnrollmentGQLModel")]
PaymentInfoGQLModel = typing.Annotated["PaymentInfoGQLModel", strawberry.lazy(".PaymentInfoGQLModel")]


@createInputs2
class AdmissionInputFilter:
    id: IDType
    applicant_name: str
    applicant_email: str
    status_id: IDType
    name: str
    name_en: str
    program_id: IDType
    payment_info_id: IDType
    applied_date: datetime.datetime
    application_start_date: datetime.datetime
    application_last_date: datetime.datetime
    end_date: datetime.datetime
    condition_date: datetime.datetime
    payment_date: datetime.datetime
    condition_extended_date: datetime.datetime
    request_condition_extend_date: datetime.datetime
    request_extra_conditions_date: datetime.datetime
    request_extra_date_date: datetime.datetime
    exam_start_date: datetime.datetime
    exam_last_date: datetime.datetime
    student_entry_date: datetime.datetime


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
    status_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="admission status id",
        permission_classes=[OnlyForAuthentized]
    )
    name: typing.Optional[str] = strawberry.field(
        default=None,
        description="admission name",
        permission_classes=[OnlyForAuthentized]
    )
    name_en: typing.Optional[str] = strawberry.field(
        default=None,
        description="admission name in English",
        permission_classes=[OnlyForAuthentized]
    )
    program_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="study program reference",
        permission_classes=[OnlyForAuthentized]
    )
    payment_info_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="payment info reference",
        permission_classes=[OnlyForAuthentized]
    )
    application_start_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="start date for applications",
        permission_classes=[OnlyForAuthentized]
    )
    application_last_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="last date for applications",
        permission_classes=[OnlyForAuthentized]
    )
    end_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="end date of admission process",
        permission_classes=[OnlyForAuthentized]
    )
    condition_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="deadline for conditions",
        permission_classes=[OnlyForAuthentized]
    )
    payment_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="deadline for payment",
        permission_classes=[OnlyForAuthentized]
    )
    condition_extended_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="extended conditions deadline",
        permission_classes=[OnlyForAuthentized]
    )
    request_condition_extend_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="deadline to request condition extension",
        permission_classes=[OnlyForAuthentized]
    )
    request_extra_conditions_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="deadline to request extra conditions",
        permission_classes=[OnlyForAuthentized]
    )
    request_extra_date_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="deadline to request extra exam date",
        permission_classes=[OnlyForAuthentized]
    )
    exam_start_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="first possible exam date",
        permission_classes=[OnlyForAuthentized]
    )
    exam_last_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="last possible exam date",
        permission_classes=[OnlyForAuthentized]
    )
    student_entry_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="student entry date",
        permission_classes=[OnlyForAuthentized]
    )

    # related enrollments
    enrollment_records: typing.List["EnrollmentGQLModel"] = strawberry.field(
        description="enrollments created from this admission",
        permission_classes=[OnlyForAuthentized],
        resolver=VectorResolver["EnrollmentGQLModel"](fkey_field_name="admission_id", whereType=EnrollmentInputFilter)
    )
    payment_info: typing.Optional["PaymentInfoGQLModel"] = strawberry.field(
        description="payment conditions for the admission",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["PaymentInfoGQLModel"](fkey_field_name="payment_info_id")
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
    applied_date: typing.Optional[datetime.datetime] = None
    status_id: typing.Optional[IDType] = None
    name: typing.Optional[str] = None
    name_en: typing.Optional[str] = None
    program_id: typing.Optional[IDType] = None
    payment_info_id: typing.Optional[IDType] = None
    application_start_date: typing.Optional[datetime.datetime] = None
    application_last_date: typing.Optional[datetime.datetime] = None
    end_date: typing.Optional[datetime.datetime] = None
    condition_date: typing.Optional[datetime.datetime] = None
    payment_date: typing.Optional[datetime.datetime] = None
    condition_extended_date: typing.Optional[datetime.datetime] = None
    request_condition_extend_date: typing.Optional[datetime.datetime] = None
    request_extra_conditions_date: typing.Optional[datetime.datetime] = None
    request_extra_date_date: typing.Optional[datetime.datetime] = None
    exam_start_date: typing.Optional[datetime.datetime] = None
    exam_last_date: typing.Optional[datetime.datetime] = None
    student_entry_date: typing.Optional[datetime.datetime] = None


@strawberry.input(description="Input model for updating an admission")
class AdmissionUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    applicant_name: typing.Optional[str] = None
    applicant_email: typing.Optional[str] = None
    applied_date: typing.Optional[datetime.datetime] = None
    status_id: typing.Optional[IDType] = None
    name: typing.Optional[str] = None
    name_en: typing.Optional[str] = None
    program_id: typing.Optional[IDType] = None
    payment_info_id: typing.Optional[IDType] = None
    application_start_date: typing.Optional[datetime.datetime] = None
    application_last_date: typing.Optional[datetime.datetime] = None
    end_date: typing.Optional[datetime.datetime] = None
    condition_date: typing.Optional[datetime.datetime] = None
    payment_date: typing.Optional[datetime.datetime] = None
    condition_extended_date: typing.Optional[datetime.datetime] = None
    request_condition_extend_date: typing.Optional[datetime.datetime] = None
    request_extra_conditions_date: typing.Optional[datetime.datetime] = None
    request_extra_date_date: typing.Optional[datetime.datetime] = None
    exam_start_date: typing.Optional[datetime.datetime] = None
    exam_last_date: typing.Optional[datetime.datetime] = None
    student_entry_date: typing.Optional[datetime.datetime] = None


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
        if admission.applied_date is None:
            admission.applied_date = db_row.applied_date
        if admission.status_id is None:
            admission.status_id = db_row.status_id
        if admission.name is None:
            admission.name = db_row.name
        if admission.name_en is None:
            admission.name_en = db_row.name_en
        if admission.program_id is None:
            admission.program_id = db_row.program_id
        if admission.payment_info_id is None:
            admission.payment_info_id = db_row.payment_info_id
        if admission.application_start_date is None:
            admission.application_start_date = db_row.application_start_date
        if admission.application_last_date is None:
            admission.application_last_date = db_row.application_last_date
        if admission.end_date is None:
            admission.end_date = db_row.end_date
        if admission.condition_date is None:
            admission.condition_date = db_row.condition_date
        if admission.payment_date is None:
            admission.payment_date = db_row.payment_date
        if admission.condition_extended_date is None:
            admission.condition_extended_date = db_row.condition_extended_date
        if admission.request_condition_extend_date is None:
            admission.request_condition_extend_date = db_row.request_condition_extend_date
        if admission.request_extra_conditions_date is None:
            admission.request_extra_conditions_date = db_row.request_extra_conditions_date
        if admission.request_extra_date_date is None:
            admission.request_extra_date_date = db_row.request_extra_date_date
        if admission.exam_start_date is None:
            admission.exam_start_date = db_row.exam_start_date
        if admission.exam_last_date is None:
            admission.exam_last_date = db_row.exam_last_date
        if admission.student_entry_date is None:
            admission.student_entry_date = db_row.student_entry_date

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
