import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import getUserFromInfo

from .BaseGQLModel import BaseGQLModel, IDType
from .admission_permissions import AdmissionsAdminPermission, is_admissions_admin
from uoishelpers.resolvers import InsertError, UpdateError
from .db_errors import integrity_error_to_error
from .pagination import resolve_page
from .validation import normalize_datetime_field
from src.services.admissions import accept_application, submit_application, withdraw_application


AdmissionProcessGQLModel = typing.Annotated["AdmissionProcessGQLModel", strawberry.lazy(".AdmissionProcessGQLModel")]
AdmissionPaymentGQLModel = typing.Annotated["AdmissionPaymentGQLModel", strawberry.lazy(".AdmissionPaymentGQLModel")]
AdmissionApplicantGQLModel = typing.Annotated["AdmissionApplicantGQLModel", strawberry.lazy(".AdmissionApplicantGQLModel")]
AdmissionOfferGQLModel = typing.Annotated["AdmissionOfferGQLModel", strawberry.lazy(".AdmissionOfferGQLModel")]


@createInputs2
class AdmissionApplicationInputFilter:
    id: IDType
    applicant_id: IDType
    applied_date: datetime.datetime
    accepted: bool
    accepted_at: datetime.datetime
    acceptedby_id: IDType
    withdrawn: bool
    withdrawn_at: datetime.datetime
    withdrawnby_id: IDType
    process_id: IDType
    payment_id: IDType
    offer_id: IDType


@strawberry.federation.type(keys=["id"], description="Admission application submitted by a user")
class AdmissionApplicationGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).AdmissionApplicationModel

    applicant_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="applicant reference",
        permission_classes=[OnlyForAuthentized]
    )
    applied_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="application date",
        permission_classes=[OnlyForAuthentized]
    )
    accepted: typing.Optional[bool] = strawberry.field(
        default=None,
        description="application accepted by study office",
        permission_classes=[OnlyForAuthentized]
    )
    accepted_at: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="acceptance date",
        permission_classes=[OnlyForAuthentized]
    )
    acceptedby_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="user who accepted application",
        permission_classes=[OnlyForAuthentized]
    )
    withdrawn: typing.Optional[bool] = strawberry.field(
        default=None,
        description="application withdrawn by applicant",
        permission_classes=[OnlyForAuthentized]
    )
    withdrawn_at: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="withdrawal date",
        permission_classes=[OnlyForAuthentized]
    )
    withdrawnby_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="user who withdrew application",
        permission_classes=[OnlyForAuthentized]
    )
    process_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="admission process reference",
        permission_classes=[OnlyForAuthentized]
    )
    payment_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="admission payment reference",
        permission_classes=[OnlyForAuthentized]
    )
    offer_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="admission offer reference",
        permission_classes=[OnlyForAuthentized]
    )

    process: typing.Optional["AdmissionProcessGQLModel"] = strawberry.field(
        description="related admission process",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["AdmissionProcessGQLModel"](fkey_field_name="process_id")
    )
    payment: typing.Optional["AdmissionPaymentGQLModel"] = strawberry.field(
        description="related admission payment",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["AdmissionPaymentGQLModel"](fkey_field_name="payment_id")
    )
    offer: typing.Optional["AdmissionOfferGQLModel"] = strawberry.field(
        description="related admission offer",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["AdmissionOfferGQLModel"](fkey_field_name="offer_id")
    )
    @strawberry.field(
        description="applicant details",
        permission_classes=[OnlyForAuthentized]
    )
    async def applicant(self) -> typing.Optional["AdmissionApplicantGQLModel"]:
        from .AdmissionApplicantGQLModel import AdmissionApplicantGQLModel

        return None if self.applicant_id is None else AdmissionApplicantGQLModel(id=self.applicant_id)


@strawberry.type(description="Admission application queries")
class AdmissionApplicationQuery:
    @strawberry.field(
        description="get admission application by id",
        permission_classes=[OnlyForAuthentized],
    )
    async def admission_application_by_id(
        self,
        info: strawberry.Info,
        id: IDType,
    ) -> typing.Optional[AdmissionApplicationGQLModel]:
        from sqlalchemy import select
        from src.DBDefinitions import AdmissionApplicantModel, AdmissionApplicationModel

        user = getUserFromInfo(info=info) or {}
        if is_admissions_admin(user):
            return await AdmissionApplicationGQLModel.load_with_loader(info=info, id=id)

        user_id = user.get("id")
        if not user_id:
            return None

        loader = AdmissionApplicationGQLModel.getLoader(info=info)
        stmt = (
            select(AdmissionApplicationModel.id)
            .join(
                AdmissionApplicantModel,
                AdmissionApplicantModel.id == AdmissionApplicationModel.applicant_id,
            )
            .where(
                AdmissionApplicationModel.id == id,
                AdmissionApplicantModel.applicant_user_id == user_id,
            )
        )
        result = await loader.session.execute(stmt)
        row_id = result.scalars().first()
        if row_id is None:
            return None
        db_row = await loader.load(row_id)
        return None if db_row is None else AdmissionApplicationGQLModel.from_dataclass(db_row)

    @strawberry.field(
        description="page of admission applications",
        permission_classes=[OnlyForAuthentized],
    )
    async def admission_application_page(
        self,
        info: strawberry.Info,
        where: typing.Optional[AdmissionApplicationInputFilter] = None,
        skip: typing.Optional[int] = 0,
        limit: typing.Optional[int] = 10,
        orderby: typing.Optional[str] = None,
        desc: typing.Optional[bool] = None,
        offset: typing.Optional[int] = None,
    ) -> typing.List[AdmissionApplicationGQLModel]:
        from sqlalchemy import select
        from src.DBDefinitions import AdmissionApplicantModel

        if offset is not None:
            skip = offset

        user = getUserFromInfo(info=info) or {}
        loader = AdmissionApplicationGQLModel.getLoader(info=info)

        if is_admissions_admin(user):
            return await resolve_page(
                info,
                AdmissionApplicationGQLModel,
                where,
                skip,
                limit,
                orderby,
                desc,
                offset,
            )

        user_id = user.get("id")
        if not user_id:
            return []

        applicant_stmt = select(AdmissionApplicantModel.id).where(
            AdmissionApplicantModel.applicant_user_id == user_id
        )
        result = await loader.session.execute(applicant_stmt)
        applicant_id = result.scalars().first()
        if applicant_id is None:
            return []

        return await resolve_page(
            info,
            AdmissionApplicationGQLModel,
            where,
            skip,
            limit,
            orderby,
            desc,
            offset,
            extendedfilter={"applicant_id": applicant_id},
        )


@strawberry.input(description="Input model for creating an admission application")
class AdmissionApplicationInsertGQLModel:
    applicant_id: typing.Optional[IDType] = None
    applied_date: typing.Optional[datetime.datetime] = None
    accepted: typing.Optional[bool] = None
    accepted_at: typing.Optional[datetime.datetime] = None
    acceptedby_id: typing.Optional[IDType] = None
    withdrawn: typing.Optional[bool] = None
    withdrawn_at: typing.Optional[datetime.datetime] = None
    withdrawnby_id: typing.Optional[IDType] = None
    process_id: typing.Optional[IDType] = None
    payment_id: typing.Optional[IDType] = None
    offer_id: typing.Optional[IDType] = None


@strawberry.input(description="Input model for updating an admission application")
class AdmissionApplicationUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    applicant_id: typing.Optional[IDType] = strawberry.UNSET
    applied_date: typing.Optional[datetime.datetime] = strawberry.UNSET
    accepted: typing.Optional[bool] = strawberry.UNSET
    accepted_at: typing.Optional[datetime.datetime] = strawberry.UNSET
    acceptedby_id: typing.Optional[IDType] = strawberry.UNSET
    withdrawn: typing.Optional[bool] = strawberry.UNSET
    withdrawn_at: typing.Optional[datetime.datetime] = strawberry.UNSET
    withdrawnby_id: typing.Optional[IDType] = strawberry.UNSET
    process_id: typing.Optional[IDType] = strawberry.UNSET
    payment_id: typing.Optional[IDType] = strawberry.UNSET
    offer_id: typing.Optional[IDType] = strawberry.UNSET


@strawberry.input(description="Input model for submitting an admission application")
class AdmissionApplicationSubmitGQLModel:
    offer_id: IDType


@strawberry.input(description="Input model for accepting an admission application")
class AdmissionApplicationAcceptGQLModel:
    application_id: IDType


@strawberry.input(description="Input model for withdrawing an admission application")
class AdmissionApplicationWithdrawGQLModel:
    application_id: IDType


@strawberry.type(description="Admission application mutations")
class AdmissionApplicationMutation:
    @strawberry.field(
        description="Insert an admission application",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission]
    )
    async def admission_application_insert(
        self,
        info: strawberry.Info,
        application: AdmissionApplicationInsertGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, InsertError[AdmissionApplicationGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Insert

        normalize_datetime_field(application, "applied_date")
        try:
            return await Insert[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=application)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                InsertError[AdmissionApplicationGQLModel],
                "admissionApplicationInsert",
                application
            )

    @strawberry.field(
        description="Update an admission application",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission]
    )
    async def admission_application_update(
        self,
        info: strawberry.Info,
        application: AdmissionApplicationUpdateGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, UpdateError[AdmissionApplicationGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Update

        normalize_datetime_field(application, "applied_date")
        try:
            return await Update[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=application)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                UpdateError[AdmissionApplicationGQLModel],
                "admissionApplicationUpdate",
                application
            )

    @strawberry.field(
        description="Submit admission application for an offer",
        permission_classes=[OnlyForAuthentized]
    )
    async def admission_application_submit(
        self,
        info: strawberry.Info,
        submission: AdmissionApplicationSubmitGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, InsertError[AdmissionApplicationGQLModel]]:
        return await submit_application(info, submission)

    @strawberry.field(
        description="Accept admission application by study office",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission]
    )
    async def admission_application_accept(
        self,
        info: strawberry.Info,
        acceptance: AdmissionApplicationAcceptGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, UpdateError[AdmissionApplicationGQLModel]]:
        return await accept_application(info, acceptance)

    @strawberry.field(
        description="Withdraw admission application by applicant",
        permission_classes=[OnlyForAuthentized]
    )
    async def admission_application_withdraw(
        self,
        info: strawberry.Info,
        withdrawal: AdmissionApplicationWithdrawGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, UpdateError[AdmissionApplicationGQLModel]]:
        return await withdraw_application(info, withdrawal)
