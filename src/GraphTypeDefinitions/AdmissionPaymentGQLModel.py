import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, createInputs2

from .BaseGQLModel import BaseGQLModel, IDType
from .admission_permissions import (
    ADMISSION_READ_PERMISSION, ADMISSION_ADMIN_PERMISSION,
    admission_field
)
from .pagination import resolve_page
from .validation import resolve_unset, validate_numeric, validate_positive, validate_required


@createInputs2
class AdmissionPaymentInputFilter:
    id: IDType
    required_amount: float
    paid_at: datetime.datetime
    bank_statement_id: IDType


@strawberry.federation.type(keys=["id"], description="Admission payment waiting for matching")
class AdmissionPaymentGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).AdmissionPaymentModel

    # Using centralized permission system
    required_amount: typing.Optional[float] = admission_field(
        default=None,
        description="required amount"
    )
    paid_at: typing.Optional[datetime.datetime] = admission_field(
        default=None,
        description="payment date"
    )
    bank_statement_id: typing.Optional[IDType] = admission_field(
        default=None,
        description="bank statement reference"
    )


@strawberry.type(description="Admission payment queries")
class AdmissionPaymentQuery:
    admission_payment_by_id: typing.Optional[AdmissionPaymentGQLModel] = strawberry.field(
        description="get admission payment by id",
        permission_classes=ADMISSION_READ_PERMISSION,
        resolver=AdmissionPaymentGQLModel.load_with_loader
    )

    @strawberry.field(
        description="page of admission payments",
        permission_classes=ADMISSION_READ_PERMISSION
    )
    async def admission_payment_page(
        self,
        info: strawberry.Info,
        where: typing.Optional[AdmissionPaymentInputFilter] = None,
        skip: typing.Optional[int] = 0,
        limit: typing.Optional[int] = 10,
        orderby: typing.Optional[str] = None,
        desc: typing.Optional[bool] = None,
        offset: typing.Optional[int] = None,
    ) -> typing.List[AdmissionPaymentGQLModel]:
        return await resolve_page(
            info,
            AdmissionPaymentGQLModel,
            where,
            skip,
            limit,
            orderby,
            desc,
            offset,
        )


from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating admission payment")
class AdmissionPaymentInsertGQLModel:
    required_amount: typing.Optional[float] = None
    paid_at: typing.Optional[datetime.datetime] = None
    bank_statement_id: typing.Optional[IDType] = None


@strawberry.input(description="Input model for updating admission payment")
class AdmissionPaymentUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    required_amount: typing.Optional[float] = strawberry.UNSET
    paid_at: typing.Optional[datetime.datetime] = strawberry.UNSET
    bank_statement_id: typing.Optional[IDType] = strawberry.UNSET


@strawberry.input(description="Input model for deleting admission payment")
class AdmissionPaymentDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


@strawberry.type(description="Admission payment mutations")
class AdmissionPaymentMutation:
    @strawberry.field(
        description="Insert admission payment",
        permission_classes=ADMISSION_ADMIN_PERMISSION
    )
    async def admission_payment_insert(
        self,
        info: strawberry.Info,
        payment: AdmissionPaymentInsertGQLModel,
    ) -> typing.Union[AdmissionPaymentGQLModel, InsertError[AdmissionPaymentGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Insert

        try:
            return await Insert[AdmissionPaymentGQLModel].DoItSafeWay(info=info, entity=payment)
        except IntegrityError as exc:
            return InsertError[AdmissionPaymentGQLModel](
                msg="Database integrity error",
                code="INTEGRITY_ERROR",
                location="admissionPaymentInsert"
            )

    @strawberry.field(
        description="Update admission payment",
        permission_classes=ADMISSION_ADMIN_PERMISSION
    )
    async def admission_payment_update(
        self,
        info: strawberry.Info,
        payment: AdmissionPaymentUpdateGQLModel,
    ) -> typing.Union[AdmissionPaymentGQLModel, UpdateError[AdmissionPaymentGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Update

        try:
            return await Update[AdmissionPaymentGQLModel].DoItSafeWay(info=info, entity=payment)
        except IntegrityError as exc:
            return UpdateError[AdmissionPaymentGQLModel](
                msg="Database integrity error",
                code="INTEGRITY_ERROR",
                location="admissionPaymentUpdate"
            )

    @strawberry.field(
        description="Delete admission payment",
        permission_classes=ADMISSION_ADMIN_PERMISSION
    )
    async def admission_payment_delete(
        self,
        info: strawberry.Info,
        payment: AdmissionPaymentDeleteGQLModel,
    ) -> typing.Union[AdmissionPaymentGQLModel, DeleteError[AdmissionPaymentGQLModel]]:
        from uoishelpers.resolvers import Delete

        return await Delete[AdmissionPaymentGQLModel].DoItSafeWay(info=info, entity=payment)
