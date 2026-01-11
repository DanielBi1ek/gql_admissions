import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType
from .admission_permissions import AdmissionsAdminPermission
from .db_errors import integrity_error_to_error


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
        if offset is not None:
            skip = offset
        loader = AdmissionBankAccountGQLModel.getLoader(info=info)
        wheredict = None if where is None else strawberry.asdict(where)
        rows = await loader.page(
            where=wheredict,
            skip=skip or 0,
            limit=limit,
            orderby=orderby,
            desc=desc,
        )
        return [AdmissionBankAccountGQLModel.from_dataclass(row) for row in rows]


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

        def _is_digits(value: str) -> bool:
            return isinstance(value, str) and value.isdigit()

        if not _is_digits(account.account_prefix):
            return InsertError[AdmissionBankAccountGQLModel](
                msg="Account prefix must be numeric",
                code="0b1f2f3b-0e76-4f86-9d93-3a8c62b4c4a1",
                location="admissionBankAccountCreate",
                _input=account
            )
        if not _is_digits(account.account_number):
            return InsertError[AdmissionBankAccountGQLModel](
                msg="Account number must be numeric",
                code="2a6b8f97-1a7c-4c3b-9b77-8f3a2c1d0f5e",
                location="admissionBankAccountCreate",
                _input=account
            )
        if not _is_digits(account.bank_code):
            return InsertError[AdmissionBankAccountGQLModel](
                msg="Bank code must be numeric",
                code="7f1f0d3e-2c1a-4bc6-8f8b-6c8f4c7a5e2d",
                location="admissionBankAccountCreate",
                _input=account
            )

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

        def _is_digits(value: str) -> bool:
            return isinstance(value, str) and value.isdigit()

        if account.account_prefix is None or account.account_number is None or account.bank_code is None:
            return InsertError[AdmissionBankAccountGQLModel](
                msg="Missing required value",
                code="a3c2a8f9-3f19-4e88-a5a0-1a7a4f6f0f8d",
                location="admissionBankAccountInsert",
                _input=account
            )
        if not _is_digits(account.account_prefix):
            return InsertError[AdmissionBankAccountGQLModel](
                msg="Account prefix must be numeric",
                code="0b1f2f3b-0e76-4f86-9d93-3a8c62b4c4a1",
                location="admissionBankAccountInsert",
                _input=account
            )
        if not _is_digits(account.account_number):
            return InsertError[AdmissionBankAccountGQLModel](
                msg="Account number must be numeric",
                code="2a6b8f97-1a7c-4c3b-9b77-8f3a2c1d0f5e",
                location="admissionBankAccountInsert",
                _input=account
            )
        if not _is_digits(account.bank_code):
            return InsertError[AdmissionBankAccountGQLModel](
                msg="Bank code must be numeric",
                code="7f1f0d3e-2c1a-4bc6-8f8b-6c8f4c7a5e2d",
                location="admissionBankAccountInsert",
                _input=account
            )

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

        def _is_digits(value: str) -> bool:
            return isinstance(value, str) and value.isdigit()

        if account.account_prefix is not strawberry.UNSET and not _is_digits(account.account_prefix):
            return UpdateError[AdmissionBankAccountGQLModel](
                msg="Account prefix must be numeric",
                code="0b1f2f3b-0e76-4f86-9d93-3a8c62b4c4a1",
                location="admissionBankAccountUpdate",
                _input=account
            )
        if account.account_number is not strawberry.UNSET and not _is_digits(account.account_number):
            return UpdateError[AdmissionBankAccountGQLModel](
                msg="Account number must be numeric",
                code="2a6b8f97-1a7c-4c3b-9b77-8f3a2c1d0f5e",
                location="admissionBankAccountUpdate",
                _input=account
            )
        if account.bank_code is not strawberry.UNSET and not _is_digits(account.bank_code):
            return UpdateError[AdmissionBankAccountGQLModel](
                msg="Bank code must be numeric",
                code="7f1f0d3e-2c1a-4bc6-8f8b-6c8f4c7a5e2d",
                location="admissionBankAccountUpdate",
                _input=account
            )

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
