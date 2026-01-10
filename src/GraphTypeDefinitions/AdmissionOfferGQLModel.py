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


@strawberry.type(description="Admission offer mutations")
class AdmissionOfferMutation:
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
