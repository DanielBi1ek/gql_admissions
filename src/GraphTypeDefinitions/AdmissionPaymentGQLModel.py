import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, createInputs2
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType
from .admission_permissions import AdmissionsAdminPermission
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

    required_amount: typing.Optional[float] = strawberry.field(
        default=None,
        description="required amount",
        permission_classes=[OnlyForAuthentized]
    )
    paid_at: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="payment date",
        permission_classes=[OnlyForAuthentized]
    )
    bank_statement_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="bank statement reference",
        permission_classes=[OnlyForAuthentized]
    )


@strawberry.type(description="Admission payment queries")
class AdmissionPaymentQuery:
    admission_payment_by_id: typing.Optional[AdmissionPaymentGQLModel] = strawberry.field(
        description="get admission payment by id",
        permission_classes=[OnlyForAuthentized],
        resolver=AdmissionPaymentGQLModel.load_with_loader
    )

    @strawberry.field(
        description="page of admission payments",
        permission_classes=[OnlyForAuthentized],
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
    @strawberry.mutation(
        description="Insert admission payment",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission],
    )
    async def admission_payment_insert(
        self,
        info: strawberry.Info,
        payment: AdmissionPaymentInsertGQLModel
    ) -> typing.Union[AdmissionPaymentGQLModel, InsertError[AdmissionPaymentGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Insert

        error = validate_required(
            payment.required_amount,
            error_cls=InsertError[AdmissionPaymentGQLModel],
            location="admissionPaymentInsert",
            input_obj=payment,
        )
        if error is not None:
            return error
        error = validate_numeric(
            payment.required_amount,
            error_cls=InsertError[AdmissionPaymentGQLModel],
            location="admissionPaymentInsert",
            input_obj=payment,
        )
        if error is not None:
            return error
        error = validate_positive(
            payment.required_amount,
            error_cls=InsertError[AdmissionPaymentGQLModel],
            location="admissionPaymentInsert",
            input_obj=payment,
        )
        if error is not None:
            return error

        try:
            return await Insert[AdmissionPaymentGQLModel].DoItSafeWay(info=info, entity=payment)
        except IntegrityError as exc:
            from .db_errors import integrity_error_to_error

            return integrity_error_to_error(
                exc,
                InsertError[AdmissionPaymentGQLModel],
                "admissionPaymentInsert",
                payment
            )

    @strawberry.mutation(
        description="Update admission payment",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission],
        extensions=[LoadDataExtension[UpdateError, AdmissionPaymentGQLModel]()]
    )
    async def admission_payment_update(
        self,
        info: strawberry.Info,
        payment: AdmissionPaymentUpdateGQLModel,
        db_row: typing.Any
    ) -> typing.Union[AdmissionPaymentGQLModel, UpdateError[AdmissionPaymentGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Update

        new_required = resolve_unset(payment.required_amount, db_row.required_amount)
        error = validate_required(
            new_required,
            error_cls=UpdateError[AdmissionPaymentGQLModel],
            location="admissionPaymentUpdate",
            input_obj=payment,
        )
        if error is not None:
            return error
        error = validate_numeric(
            new_required,
            error_cls=UpdateError[AdmissionPaymentGQLModel],
            location="admissionPaymentUpdate",
            input_obj=payment,
        )
        if error is not None:
            return error
        error = validate_positive(
            new_required,
            error_cls=UpdateError[AdmissionPaymentGQLModel],
            location="admissionPaymentUpdate",
            input_obj=payment,
        )
        if error is not None:
            return error

        try:
            return await Update[AdmissionPaymentGQLModel].DoItSafeWay(info=info, entity=payment)
        except IntegrityError as exc:
            from .db_errors import integrity_error_to_error

            return integrity_error_to_error(
                exc,
                UpdateError[AdmissionPaymentGQLModel],
                "admissionPaymentUpdate",
                payment
            )

    @strawberry.mutation(
        description="Delete admission payment",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission],
        extensions=[LoadDataExtension[DeleteError, AdmissionPaymentGQLModel]()]
    )
    async def admission_payment_delete(
        self,
        info: strawberry.Info,
        payment: AdmissionPaymentDeleteGQLModel,
        db_row: typing.Any
    ) -> typing.Optional[DeleteError[AdmissionPaymentGQLModel]]:
        from uoishelpers.resolvers import Delete

        return await Delete[AdmissionPaymentGQLModel].DoItSafeWay(info=info, entity=payment)
