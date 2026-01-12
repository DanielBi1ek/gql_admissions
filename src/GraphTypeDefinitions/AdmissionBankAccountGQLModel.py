import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, createInputs2
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType
from .admission_permissions import AdmissionsAdminPermission
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

    account_prefix: typing.Optional[str] = strawberry.field(
        default=None,
        description="bank account prefix",
        permission_classes=[OnlyForAuthentized]
    )
    account_number: typing.Optional[str] = strawberry.field(
        default=None,
        description="bank account number",
        permission_classes=[OnlyForAuthentized]
    )
    bank_code: typing.Optional[str] = strawberry.field(
        default=None,
        description="bank code",
        permission_classes=[OnlyForAuthentized]
    )
    description: typing.Optional[str] = strawberry.field(
        default=None,
        description="bank account description",
        permission_classes=[OnlyForAuthentized]
    )


@strawberry.type(description="Admission bank account queries")
class AdmissionBankAccountQuery:
    admission_bank_account_by_id: typing.Optional[AdmissionBankAccountGQLModel] = strawberry.field(
        description="get admission bank account by id",
        permission_classes=[OnlyForAuthentized],
        resolver=AdmissionBankAccountGQLModel.load_with_loader
    )

    @strawberry.field(
        description="page of admission bank accounts",
        permission_classes=[OnlyForAuthentized],
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


@strawberry.input(description="Input model for creating admission bank account with validation")
class AdmissionBankAccountCreateGQLModel:
    account_prefix: str
    account_number: str
    bank_code: str
    description: typing.Optional[str] = None


@strawberry.type(description="Admission bank account mutations")
class AdmissionBankAccountMutation:
    @strawberry.mutation(
        description="Create admission bank account with validation",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission]
    )
    async def admission_bank_account_create(
        self,
        info: strawberry.Info,
        account: AdmissionBankAccountCreateGQLModel
    ) -> typing.Union[AdmissionBankAccountGQLModel, InsertError[AdmissionBankAccountGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Insert

        error = validate_digits(
            account.account_prefix,
            error_cls=InsertError[AdmissionBankAccountGQLModel],
            location="admissionBankAccountCreate",
            input_obj=account,
            msg="Account prefix must be numeric",
            code=codes.ERR_ACCOUNT_PREFIX_NUMERIC,
        )
        if error is not None:
            return error
        error = validate_digits(
            account.account_number,
            error_cls=InsertError[AdmissionBankAccountGQLModel],
            location="admissionBankAccountCreate",
            input_obj=account,
            msg="Account number must be numeric",
            code=codes.ERR_ACCOUNT_NUMBER_NUMERIC,
        )
        if error is not None:
            return error
        error = validate_digits(
            account.bank_code,
            error_cls=InsertError[AdmissionBankAccountGQLModel],
            location="admissionBankAccountCreate",
            input_obj=account,
            msg="Bank code must be numeric",
            code=codes.ERR_BANK_CODE_NUMERIC,
        )
        if error is not None:
            return error

        entity = AdmissionBankAccountInsertGQLModel(
            account_prefix=account.account_prefix,
            account_number=account.account_number,
            bank_code=account.bank_code,
            description=account.description
        )
        try:
            return await Insert[AdmissionBankAccountGQLModel].DoItSafeWay(info=info, entity=entity)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                InsertError[AdmissionBankAccountGQLModel],
                "admissionBankAccountCreate",
                account
            )

    @strawberry.mutation(
        description="Insert admission bank account",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission]
    )
    async def admission_bank_account_insert(
        self,
        info: strawberry.Info,
        account: AdmissionBankAccountInsertGQLModel
    ) -> typing.Union[AdmissionBankAccountGQLModel, InsertError[AdmissionBankAccountGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Insert

        if account.account_prefix is None or account.account_number is None or account.bank_code is None:
            return build_error(
                InsertError[AdmissionBankAccountGQLModel],
                msg="Missing required value",
                code=codes.ERR_MISSING_REQUIRED,
                location="admissionBankAccountInsert",
                input_obj=account,
            )
        error = validate_digits(
            account.account_prefix,
            error_cls=InsertError[AdmissionBankAccountGQLModel],
            location="admissionBankAccountInsert",
            input_obj=account,
            msg="Account prefix must be numeric",
            code=codes.ERR_ACCOUNT_PREFIX_NUMERIC,
        )
        if error is not None:
            return error
        error = validate_digits(
            account.account_number,
            error_cls=InsertError[AdmissionBankAccountGQLModel],
            location="admissionBankAccountInsert",
            input_obj=account,
            msg="Account number must be numeric",
            code=codes.ERR_ACCOUNT_NUMBER_NUMERIC,
        )
        if error is not None:
            return error
        error = validate_digits(
            account.bank_code,
            error_cls=InsertError[AdmissionBankAccountGQLModel],
            location="admissionBankAccountInsert",
            input_obj=account,
            msg="Bank code must be numeric",
            code=codes.ERR_BANK_CODE_NUMERIC,
        )
        if error is not None:
            return error

        try:
            return await Insert[AdmissionBankAccountGQLModel].DoItSafeWay(info=info, entity=account)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                InsertError[AdmissionBankAccountGQLModel],
                "admissionBankAccountInsert",
                account
            )

    @strawberry.mutation(
        description="Update admission bank account",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission],
        extensions=[LoadDataExtension[UpdateError, AdmissionBankAccountGQLModel]()]
    )
    async def admission_bank_account_update(
        self,
        info: strawberry.Info,
        account: AdmissionBankAccountUpdateGQLModel,
        db_row: typing.Any
    ) -> typing.Union[AdmissionBankAccountGQLModel, UpdateError[AdmissionBankAccountGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Update

        if account.account_prefix is not strawberry.UNSET:
            error = validate_digits(
                account.account_prefix,
                error_cls=UpdateError[AdmissionBankAccountGQLModel],
                location="admissionBankAccountUpdate",
                input_obj=account,
                msg="Account prefix must be numeric",
                code=codes.ERR_ACCOUNT_PREFIX_NUMERIC,
            )
            if error is not None:
                return error
        if account.account_number is not strawberry.UNSET:
            error = validate_digits(
                account.account_number,
                error_cls=UpdateError[AdmissionBankAccountGQLModel],
                location="admissionBankAccountUpdate",
                input_obj=account,
                msg="Account number must be numeric",
                code=codes.ERR_ACCOUNT_NUMBER_NUMERIC,
            )
            if error is not None:
                return error
        if account.bank_code is not strawberry.UNSET:
            error = validate_digits(
                account.bank_code,
                error_cls=UpdateError[AdmissionBankAccountGQLModel],
                location="admissionBankAccountUpdate",
                input_obj=account,
                msg="Bank code must be numeric",
                code=codes.ERR_BANK_CODE_NUMERIC,
            )
            if error is not None:
                return error

        try:
            return await Update[AdmissionBankAccountGQLModel].DoItSafeWay(info=info, entity=account)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                UpdateError[AdmissionBankAccountGQLModel],
                "admissionBankAccountUpdate",
                account
            )

    @strawberry.mutation(
        description="Delete admission bank account",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission],
        extensions=[LoadDataExtension[DeleteError, AdmissionBankAccountGQLModel]()]
    )
    async def admission_bank_account_delete(
        self,
        info: strawberry.Info,
        account: AdmissionBankAccountDeleteGQLModel,
        db_row: typing.Any
    ) -> typing.Optional[DeleteError[AdmissionBankAccountGQLModel]]:
        from uoishelpers.resolvers import Delete

        return await Delete[AdmissionBankAccountGQLModel].DoItSafeWay(info=info, entity=account)
