import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, createInputs2

from .BaseGQLModel import BaseGQLModel, IDType
from .admission_permissions import (
    ADMISSION_READ_PERMISSION, ADMISSION_ADMIN_PERMISSION,
    admission_field
)
from .db_errors import integrity_error_to_error
from .pagination import resolve_page
from .validation import build_error, validate_digits
from . import error_codes as codes


@createInputs2
class AdmissionBankAccountInputFilter:
    id: IDType
    account_prefix: str
    account_number: str
    bank_code: str
    description: str


@strawberry.federation.type(keys=["id"], description="Bank account used for admission payments")
class AdmissionBankAccountGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).AdmissionBankAccountModel

    # Using centralized permission system
    account_prefix: typing.Optional[str] = admission_field(
        default=None,
        description="bank account prefix"
    )
    account_number: typing.Optional[str] = admission_field(
        default=None,
        description="bank account number"
    )
    bank_code: typing.Optional[str] = admission_field(
        default=None,
        description="bank code"
    )
    description: typing.Optional[str] = admission_field(
        default=None,
        description="bank account description"
    )


@strawberry.type(description="Admission bank account queries")
class AdmissionBankAccountQuery:
    admission_bank_account_by_id: typing.Optional[AdmissionBankAccountGQLModel] = strawberry.field(
        description="get admission bank account by id",
        permission_classes=ADMISSION_READ_PERMISSION,
        resolver=AdmissionBankAccountGQLModel.load_with_loader
    )

    @strawberry.field(
        description="page of admission bank accounts",
        permission_classes=ADMISSION_READ_PERMISSION
    )
    async def admission_bank_account_page(
        self,
        info: strawberry.Info,
        where: typing.Optional[AdmissionBankAccountInputFilter] = None,
        skip: typing.Optional[int] = 0,
        limit: typing.Optional[int] = 10,
        orderby: typing.Optional[str] = None,
        desc: typing.Optional[bool] = None,
        offset: typing.Optional[int] = None,
    ) -> typing.List[AdmissionBankAccountGQLModel]:
        return await resolve_page(
            info,
            AdmissionBankAccountGQLModel,
            where,
            skip,
            limit,
            orderby,
            desc,
            offset,
        )


from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating admission bank account")
class AdmissionBankAccountInsertGQLModel:
    account_prefix: typing.Optional[str] = None
    account_number: typing.Optional[str] = None
    bank_code: typing.Optional[str] = None
    description: typing.Optional[str] = None


@strawberry.input(description="Input model for updating admission bank account")
class AdmissionBankAccountUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    account_prefix: typing.Optional[str] = strawberry.UNSET
    account_number: typing.Optional[str] = strawberry.UNSET
    bank_code: typing.Optional[str] = strawberry.UNSET
    description: typing.Optional[str] = strawberry.UNSET


@strawberry.input(description="Input model for deleting admission bank account")
class AdmissionBankAccountDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


@strawberry.type(description="Admission bank account mutations")
class AdmissionBankAccountMutation:
    @strawberry.field(
        description="Insert admission bank account",
        permission_classes=ADMISSION_ADMIN_PERMISSION
    )
    async def admission_bank_account_insert(
        self,
        info: strawberry.Info,
        bank_account: AdmissionBankAccountInsertGQLModel,
    ) -> typing.Union[AdmissionBankAccountGQLModel, InsertError[AdmissionBankAccountGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Insert

        # Validate required fields and format
        if bank_account.account_number is None or bank_account.bank_code is None:
            return build_error(
                InsertError[AdmissionBankAccountGQLModel],
                msg="Account number and bank code are required",
                code=codes.ERR_MISSING_REQUIRED,
                location="admissionBankAccountInsert",
                input_obj=bank_account,
            )

        # Validate digits format
        error = validate_digits(
            bank_account.account_number,
            error_cls=InsertError[AdmissionBankAccountGQLModel],
            location="admissionBankAccountInsert",
            input_obj=bank_account,
            msg="Account number must contain digits only",
            code=codes.ERR_ACCOUNT_NUMBER_NUMERIC,
        )
        if error is not None:
            return error

        error = validate_digits(
            bank_account.bank_code,
            error_cls=InsertError[AdmissionBankAccountGQLModel],
            location="admissionBankAccountInsert",
            input_obj=bank_account,
            msg="Bank code must contain digits only",
            code=codes.ERR_BANK_CODE_NUMERIC,
        )
        if error is not None:
            return error

        # Validate uniqueness explicitly to avoid failing at transaction commit time.
        loader = getLoadersFromInfo(info).AdmissionBankAccountModel
        existing_rows = await loader.page(
            skip=0,
            limit=1,
            extendedfilter={
                "account_prefix": bank_account.account_prefix,
                "account_number": bank_account.account_number,
                "bank_code": bank_account.bank_code,
            },
        )
        if existing_rows:
            return build_error(
                InsertError[AdmissionBankAccountGQLModel],
                msg="Bank account already exists",
                code=codes.ERR_BANK_ACCOUNT_EXISTS,
                location="admissionBankAccountInsert",
                input_obj=bank_account,
            )

        try:
            result = await Insert[AdmissionBankAccountGQLModel].DoItSafeWay(info=info, entity=bank_account)
            if isinstance(result, InsertError):
                message = (result.msg or "").lower()
                if "integrityerror" in message or "constraint failed" in message:
                    await loader.session.rollback()
                    context_session = info.context.get("_session") or info.context.get("session")
                    if context_session is not None and context_session is not loader.session:
                        await context_session.rollback()
                    info.context["_transaction_failed"] = True
            return result
        except IntegrityError as exc:
            await loader.session.rollback()
            context_session = info.context.get("_session") or info.context.get("session")
            if context_session is not None and context_session is not loader.session:
                await context_session.rollback()
            info.context["_transaction_failed"] = True
            return integrity_error_to_error(
                exc,
                InsertError[AdmissionBankAccountGQLModel],
                "admissionBankAccountInsert",
                bank_account
            )

    @strawberry.field(
        description="Update admission bank account",
        permission_classes=ADMISSION_ADMIN_PERMISSION
    )
    async def admission_bank_account_update(
        self,
        info: strawberry.Info,
        bank_account: AdmissionBankAccountUpdateGQLModel,
    ) -> typing.Union[AdmissionBankAccountGQLModel, UpdateError[AdmissionBankAccountGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Update

        try:
            return await Update[AdmissionBankAccountGQLModel].DoItSafeWay(info=info, entity=bank_account)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                UpdateError[AdmissionBankAccountGQLModel],
                "admissionBankAccountUpdate",
                bank_account
            )

    @strawberry.field(
        description="Delete admission bank account",
        permission_classes=ADMISSION_ADMIN_PERMISSION
    )
    async def admission_bank_account_delete(
        self,
        info: strawberry.Info,
        bank_account: AdmissionBankAccountDeleteGQLModel,
    ) -> typing.Union[AdmissionBankAccountGQLModel, DeleteError[AdmissionBankAccountGQLModel]]:
        from uoishelpers.resolvers import Delete

        return await Delete[AdmissionBankAccountGQLModel].DoItSafeWay(info=info, entity=bank_account)
