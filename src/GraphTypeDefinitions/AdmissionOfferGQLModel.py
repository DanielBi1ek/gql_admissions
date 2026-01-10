import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType

AdmissionPaymentInfoGQLModel = typing.Annotated["AdmissionPaymentInfoGQLModel", strawberry.lazy(".AdmissionPaymentInfoGQLModel")]
StudyProgramGQLModel = typing.Annotated["StudyProgramGQLModel", strawberry.lazy(".StudyProgramGQLModel")]


@createInputs2
class AdmissionOfferInputFilter:
    id: IDType
    program_id: IDType
    application_start_date: datetime.datetime
    application_end_date: datetime.datetime
    payment_info_id: IDType


@strawberry.federation.type(keys=["id"], description="Admission offer for a study program")
class AdmissionOfferGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).AdmissionOfferModel

    program_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="study program reference",
        permission_classes=[OnlyForAuthentized]
    )
    application_start_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="application start",
        permission_classes=[OnlyForAuthentized]
    )
    application_end_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="application end",
        permission_classes=[OnlyForAuthentized]
    )
    payment_info_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="payment info reference",
        permission_classes=[OnlyForAuthentized]
    )

    payment_info: typing.Optional["AdmissionPaymentInfoGQLModel"] = strawberry.field(
        description="payment info",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["AdmissionPaymentInfoGQLModel"](fkey_field_name="payment_info_id")
    )
    program: typing.Optional["StudyProgramGQLModel"] = strawberry.field(
        description="study program details",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["StudyProgramGQLModel"](fkey_field_name="program_id")
    )


@strawberry.type(description="Admission offer queries")
class AdmissionOfferQuery:
    admission_offer_by_id: typing.Optional[AdmissionOfferGQLModel] = strawberry.field(
        description="get admission offer by id",
        permission_classes=[OnlyForAuthentized],
        resolver=AdmissionOfferGQLModel.load_with_loader
    )

    admission_offer_page: typing.List[AdmissionOfferGQLModel] = strawberry.field(
        description="page of admission offers",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[AdmissionOfferGQLModel](whereType=AdmissionOfferInputFilter)
    )


from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating an admission offer")
class AdmissionOfferInsertGQLModel:
    program_id: typing.Optional[IDType] = None
    application_start_date: typing.Optional[datetime.datetime] = None
    application_end_date: typing.Optional[datetime.datetime] = None
    payment_info_id: typing.Optional[IDType] = None


@strawberry.input(description="Input model for updating an admission offer")
class AdmissionOfferUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    program_id: typing.Optional[IDType] = None
    application_start_date: typing.Optional[datetime.datetime] = None
    application_end_date: typing.Optional[datetime.datetime] = None
    payment_info_id: typing.Optional[IDType] = None


@strawberry.input(description="Input model for deleting an admission offer")
class AdmissionOfferDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


@strawberry.input(description="Input model for creating an admission offer with validation")
class AdmissionOfferCreateGQLModel:
    program_id: IDType
    application_start_date: datetime.datetime
    application_end_date: datetime.datetime
    payment_info_id: IDType


@strawberry.type(description="Admission offer mutations")
class AdmissionOfferMutation:
    @strawberry.mutation(
        description="Create an admission offer with validation",
        permission_classes=[OnlyForAuthentized]
    )
    async def admission_offer_create(
        self,
        info: strawberry.Info,
        admission_offer: AdmissionOfferCreateGQLModel
    ) -> typing.Union[AdmissionOfferGQLModel, InsertError[AdmissionOfferGQLModel]]:
        from sqlalchemy import select
        from uoishelpers.resolvers import Insert
        from src.DBDefinitions import AdmissionOfferModel

        def _to_naive(value: datetime.datetime) -> datetime.datetime:
            if value.tzinfo is not None and value.utcoffset() is not None:
                return value.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            return value

        start_date = _to_naive(admission_offer.application_start_date)
        end_date = _to_naive(admission_offer.application_end_date)
        if end_date <= start_date:
            return InsertError[AdmissionOfferGQLModel](
                msg="Application end date must be after start date",
                code="b3c57cc6-4f34-4d0d-b7a8-5a47f4d58278",
                location="admissionOfferCreate",
                _input=admission_offer
            )
        if end_date.date() == start_date.date():
            return InsertError[AdmissionOfferGQLModel](
                msg="Application start and end date must not be on the same day",
                code="c9c2f2b5-7b8b-49cf-9c73-1264f2b5353f",
                location="admissionOfferCreate",
                _input=admission_offer
            )

        program_loader = getLoadersFromInfo(info).StudyProgramModel
        program = await program_loader.load(admission_offer.program_id)
        if program is None:
            return InsertError[AdmissionOfferGQLModel](
                msg="Study program not found",
                code="22a16a6a-0b62-4d0f-bb69-4efee7c2e1f9",
                location="admissionOfferCreate",
                _input=admission_offer
            )

        payment_info_loader = getLoadersFromInfo(info).AdmissionPaymentInfoModel
        payment_info = await payment_info_loader.load(admission_offer.payment_info_id)
        if payment_info is None:
            return InsertError[AdmissionOfferGQLModel](
                msg="Payment info not found",
                code="5e6d8de6-f74c-4e0a-9f20-2d4f25d5ac3b",
                location="admissionOfferCreate",
                _input=admission_offer
            )

        offer_loader = getLoadersFromInfo(info).AdmissionOfferModel
        stmt = select(AdmissionOfferModel.id).where(
            AdmissionOfferModel.program_id == admission_offer.program_id
        )
        result = await offer_loader.session.execute(stmt)
        if result.scalars().first() is not None:
            return InsertError[AdmissionOfferGQLModel](
                msg="Offer already exists for this study program",
                code="c6f27c8c-33d8-4cd0-a76a-5eb3f4a59262",
                location="admissionOfferCreate",
                _input=admission_offer
            )

        entity = AdmissionOfferInsertGQLModel(
            program_id=admission_offer.program_id,
            application_start_date=start_date,
            application_end_date=end_date,
            payment_info_id=admission_offer.payment_info_id
        )
        return await Insert[AdmissionOfferGQLModel].DoItSafeWay(info=info, entity=entity)

    @strawberry.mutation(description="Insert an admission offer", permission_classes=[OnlyForAuthentized])
    async def admission_offer_insert(
        self,
        info: strawberry.Info,
        admission_offer: AdmissionOfferInsertGQLModel
    ) -> typing.Union[AdmissionOfferGQLModel, InsertError[AdmissionOfferGQLModel]]:
        from uoishelpers.resolvers import Insert

        return await Insert[AdmissionOfferGQLModel].DoItSafeWay(info=info, entity=admission_offer)

    @strawberry.mutation(
        description="Update an admission offer",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[UpdateError, AdmissionOfferGQLModel]()]
    )
    async def admission_offer_update(
        self,
        info: strawberry.Info,
        admission_offer: AdmissionOfferUpdateGQLModel,
        db_row: typing.Any
    ) -> typing.Union[AdmissionOfferGQLModel, UpdateError[AdmissionOfferGQLModel]]:
        from uoishelpers.resolvers import Update

        return await Update[AdmissionOfferGQLModel].DoItSafeWay(info=info, entity=admission_offer)

    @strawberry.mutation(
        description="Delete an admission offer",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[DeleteError, AdmissionOfferGQLModel]()]
    )
    async def admission_offer_delete(
        self,
        info: strawberry.Info,
        admission_offer: AdmissionOfferDeleteGQLModel,
        db_row: typing.Any
    ) -> typing.Optional[DeleteError[AdmissionOfferGQLModel]]:
        from uoishelpers.resolvers import Delete

        return await Delete[AdmissionOfferGQLModel].DoItSafeWay(info=info, entity=admission_offer)
