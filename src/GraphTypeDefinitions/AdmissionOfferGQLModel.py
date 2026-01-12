import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType
from .admission_permissions import AdmissionsAdminPermission
from .db_errors import integrity_error_to_error
from .pagination import resolve_page
from .validation import build_error, to_naive_datetime
from . import error_codes as codes

AdmissionPaymentInfoGQLModel = typing.Annotated["AdmissionPaymentInfoGQLModel", strawberry.lazy(".AdmissionPaymentInfoGQLModel")]
StudyProgramGQLModel = typing.Annotated["StudyProgramGQLModel", strawberry.lazy(".StudyProgramGQLModel")]


async def _validate_offer_data(
    *,
    info: strawberry.Info,
    program_id: typing.Optional[IDType],
    payment_info_id: typing.Optional[IDType],
    start_date: typing.Optional[datetime.datetime],
    end_date: typing.Optional[datetime.datetime],
    location: str,
    input_obj: typing.Any,
    existing_offer_id: typing.Optional[IDType] = None,
    error_cls=typing.Any,
):
    from sqlalchemy import select
    from src.DBDefinitions import AdmissionOfferModel

    if program_id is None or payment_info_id is None or start_date is None or end_date is None:
        return build_error(
            error_cls,
            msg="Missing required value",
            code=codes.ERR_MISSING_REQUIRED,
            location=location,
            input_obj=input_obj,
        )

    start_date = to_naive_datetime(start_date)
    end_date = to_naive_datetime(end_date)
    if end_date <= start_date:
        return build_error(
            error_cls,
            msg="Application end date must be after start date",
            code=codes.ERR_OFFER_END_BEFORE_START,
            location=location,
            input_obj=input_obj,
        )
    if end_date.date() == start_date.date():
        return build_error(
            error_cls,
            msg="Application start and end date must not be on the same day",
            code=codes.ERR_OFFER_SAME_DAY,
            location=location,
            input_obj=input_obj,
        )

    program_loader = getLoadersFromInfo(info).StudyProgramModel
    program = await program_loader.load(program_id)
    if program is None:
        return build_error(
            error_cls,
            msg="Study program not found",
            code=codes.ERR_STUDY_PROGRAM_NOT_FOUND,
            location=location,
            input_obj=input_obj,
        )

    payment_info_loader = getLoadersFromInfo(info).AdmissionPaymentInfoModel
    payment_info = await payment_info_loader.load(payment_info_id)
    if payment_info is None:
        return build_error(
            error_cls,
            msg="Payment info not found",
            code=codes.ERR_PAYMENT_INFO_NOT_FOUND,
            location=location,
            input_obj=input_obj,
        )

    offer_loader = getLoadersFromInfo(info).AdmissionOfferModel
    stmt = select(AdmissionOfferModel.id).where(
        AdmissionOfferModel.program_id == program_id
    )
    if existing_offer_id is not None:
        stmt = stmt.where(AdmissionOfferModel.id != existing_offer_id)
    result = await offer_loader.session.execute(stmt)
    if result.scalars().first() is not None:
        return build_error(
            error_cls,
            msg="Offer already exists for this study program",
            code=codes.ERR_OFFER_EXISTS,
            location=location,
            input_obj=input_obj,
        )

    return None


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

    @strawberry.field(
        description="page of admission offers",
        permission_classes=[OnlyForAuthentized],
    )
    async def admission_offer_page(
        self,
        info: strawberry.Info,
        where: typing.Optional[AdmissionOfferInputFilter] = None,
        skip: typing.Optional[int] = 0,
        limit: typing.Optional[int] = 10,
        orderby: typing.Optional[str] = None,
        desc: typing.Optional[bool] = None,
        offset: typing.Optional[int] = None,
    ) -> typing.List[AdmissionOfferGQLModel]:
        return await resolve_page(
            info,
            AdmissionOfferGQLModel,
            where,
            skip,
            limit,
            orderby,
            desc,
            offset,
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
    program_id: typing.Optional[IDType] = strawberry.UNSET
    application_start_date: typing.Optional[datetime.datetime] = strawberry.UNSET
    application_end_date: typing.Optional[datetime.datetime] = strawberry.UNSET
    payment_info_id: typing.Optional[IDType] = strawberry.UNSET


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
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission]
    )
    async def admission_offer_create(
        self,
        info: strawberry.Info,
        admission_offer: AdmissionOfferCreateGQLModel
    ) -> typing.Union[AdmissionOfferGQLModel, InsertError[AdmissionOfferGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Insert

        validation_error = await _validate_offer_data(
            info=info,
            program_id=admission_offer.program_id,
            payment_info_id=admission_offer.payment_info_id,
            start_date=admission_offer.application_start_date,
            end_date=admission_offer.application_end_date,
            location="admissionOfferCreate",
            input_obj=admission_offer,
            error_cls=InsertError[AdmissionOfferGQLModel],
        )
        if validation_error is not None:
            return validation_error

        entity = AdmissionOfferInsertGQLModel(
            program_id=admission_offer.program_id,
            application_start_date=to_naive_datetime(admission_offer.application_start_date),
            application_end_date=to_naive_datetime(admission_offer.application_end_date),
            payment_info_id=admission_offer.payment_info_id
        )
        try:
            return await Insert[AdmissionOfferGQLModel].DoItSafeWay(info=info, entity=entity)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                InsertError[AdmissionOfferGQLModel],
                "admissionOfferCreate",
                admission_offer
            )

    @strawberry.mutation(
        description="Insert an admission offer",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission]
    )
    async def admission_offer_insert(
        self,
        info: strawberry.Info,
        admission_offer: AdmissionOfferInsertGQLModel
    ) -> typing.Union[AdmissionOfferGQLModel, InsertError[AdmissionOfferGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Insert

        validation_error = await _validate_offer_data(
            info=info,
            program_id=admission_offer.program_id,
            payment_info_id=admission_offer.payment_info_id,
            start_date=admission_offer.application_start_date,
            end_date=admission_offer.application_end_date,
            location="admissionOfferInsert",
            input_obj=admission_offer,
            error_cls=InsertError[AdmissionOfferGQLModel],
        )
        if validation_error is not None:
            return validation_error

        admission_offer.application_start_date = to_naive_datetime(admission_offer.application_start_date)
        admission_offer.application_end_date = to_naive_datetime(admission_offer.application_end_date)
        try:
            return await Insert[AdmissionOfferGQLModel].DoItSafeWay(info=info, entity=admission_offer)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                InsertError[AdmissionOfferGQLModel],
                "admissionOfferInsert",
                admission_offer
            )

    @strawberry.mutation(
        description="Update an admission offer",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission],
        extensions=[LoadDataExtension[UpdateError, AdmissionOfferGQLModel]()]
    )
    async def admission_offer_update(
        self,
        info: strawberry.Info,
        admission_offer: AdmissionOfferUpdateGQLModel,
        db_row: typing.Any
    ) -> typing.Union[AdmissionOfferGQLModel, UpdateError[AdmissionOfferGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Update

        new_program_id = db_row.program_id if admission_offer.program_id is strawberry.UNSET else admission_offer.program_id
        new_payment_info_id = db_row.payment_info_id if admission_offer.payment_info_id is strawberry.UNSET else admission_offer.payment_info_id
        new_start_date = db_row.application_start_date if admission_offer.application_start_date is strawberry.UNSET else admission_offer.application_start_date
        new_end_date = db_row.application_end_date if admission_offer.application_end_date is strawberry.UNSET else admission_offer.application_end_date

        validation_error = await _validate_offer_data(
            info=info,
            program_id=new_program_id,
            payment_info_id=new_payment_info_id,
            start_date=new_start_date,
            end_date=new_end_date,
            location="admissionOfferUpdate",
            input_obj=admission_offer,
            existing_offer_id=db_row.id,
            error_cls=UpdateError[AdmissionOfferGQLModel],
        )
        if validation_error is not None:
            return validation_error

        if admission_offer.application_start_date is not strawberry.UNSET:
            admission_offer.application_start_date = to_naive_datetime(admission_offer.application_start_date)
        if admission_offer.application_end_date is not strawberry.UNSET:
            admission_offer.application_end_date = to_naive_datetime(admission_offer.application_end_date)

        try:
            return await Update[AdmissionOfferGQLModel].DoItSafeWay(info=info, entity=admission_offer)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                UpdateError[AdmissionOfferGQLModel],
                "admissionOfferUpdate",
                admission_offer
            )

    @strawberry.mutation(
        description="Delete an admission offer",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission],
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
