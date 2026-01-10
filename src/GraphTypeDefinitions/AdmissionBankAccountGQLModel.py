import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType


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

    admission_bank_account_page: typing.List[AdmissionBankAccountGQLModel] = strawberry.field(
        description="page of admission bank accounts",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[AdmissionBankAccountGQLModel](whereType=AdmissionBankAccountInputFilter)
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
    account_prefix: typing.Optional[str] = None
    account_number: typing.Optional[str] = None
    bank_code: typing.Optional[str] = None
    description: typing.Optional[str] = None


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
        permission_classes=[OnlyForAuthentized]
    )
    async def admission_bank_account_create(
        self,
        info: strawberry.Info,
        account: AdmissionBankAccountCreateGQLModel
    ) -> typing.Union[AdmissionBankAccountGQLModel, InsertError[AdmissionBankAccountGQLModel]]:
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
                code="4c9f1d3a-5f1b-4b6e-9b62-5aef2c8e5c1c",
                location="admissionBankAccountCreate",
                _input=account
            )

        entity = AdmissionBankAccountInsertGQLModel(
            account_prefix=account.account_prefix,
            account_number=account.account_number,
            bank_code=account.bank_code,
            description=account.description
        )
        return await Insert[AdmissionBankAccountGQLModel].DoItSafeWay(info=info, entity=entity)

    @strawberry.mutation(description="Insert admission bank account", permission_classes=[OnlyForAuthentized])
    async def admission_bank_account_insert(
        self,
        info: strawberry.Info,
        account: AdmissionBankAccountInsertGQLModel
    ) -> typing.Union[AdmissionBankAccountGQLModel, InsertError[AdmissionBankAccountGQLModel]]:
        from uoishelpers.resolvers import Insert

        return await Insert[AdmissionBankAccountGQLModel].DoItSafeWay(info=info, entity=account)

    @strawberry.mutation(
        description="Update admission bank account",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[UpdateError, AdmissionBankAccountGQLModel]()]
    )
    async def admission_bank_account_update(
        self,
        info: strawberry.Info,
        account: AdmissionBankAccountUpdateGQLModel,
        db_row: typing.Any
    ) -> typing.Union[AdmissionBankAccountGQLModel, UpdateError[AdmissionBankAccountGQLModel]]:
        from uoishelpers.resolvers import Update

        return await Update[AdmissionBankAccountGQLModel].DoItSafeWay(info=info, entity=account)

    @strawberry.mutation(
        description="Delete admission bank account",
        permission_classes=[OnlyForAuthentized],
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
