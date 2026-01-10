import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import getUserFromInfo

from .BaseGQLModel import BaseGQLModel, IDType
from .unified_rbac_extensions import (
    create_insert_permissions,
    create_update_permissions,
    create_delete_permissions,
    EDITOR_ROLES,
    ADMIN_ROLES,
)
from uoishelpers.resolvers import InsertError, UpdateError, DeleteError


AdmissionProcessGQLModel = typing.Annotated["AdmissionProcessGQLModel", strawberry.lazy(".AdmissionProcessGQLModel")]
AdmissionPaymentGQLModel = typing.Annotated["AdmissionPaymentGQLModel", strawberry.lazy(".AdmissionPaymentGQLModel")]
AdmissionApplicantGQLModel = typing.Annotated["AdmissionApplicantGQLModel", strawberry.lazy(".AdmissionApplicantGQLModel")]
AdmissionOfferGQLModel = typing.Annotated["AdmissionOfferGQLModel", strawberry.lazy(".AdmissionOfferGQLModel")]


def _normalize_applied_date(entity: typing.Any) -> None:
    if not hasattr(entity, "applied_date"):
        return
    value = entity.applied_date
    if value is None or value is strawberry.UNSET:
        return
    if value.tzinfo is not None and value.utcoffset() is not None:
        entity.applied_date = value.astimezone(datetime.timezone.utc).replace(tzinfo=None)


@createInputs2
class AdmissionApplicationInputFilter:
    id: IDType
    applicant_id: IDType
    applied_date: datetime.datetime
    accepted: bool
    accepted_at: datetime.datetime
    acceptedby_id: IDType
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
    admission_application_by_id: typing.Optional[AdmissionApplicationGQLModel] = strawberry.field(
        description="get admission application by id",
        permission_classes=[OnlyForAuthentized],
        resolver=AdmissionApplicationGQLModel.load_with_loader
    )

    admission_application_page: typing.List[AdmissionApplicationGQLModel] = strawberry.field(
        description="page of admission applications",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[AdmissionApplicationGQLModel](whereType=AdmissionApplicationInputFilter)
    )


@strawberry.input(description="Input model for creating an admission application")
class AdmissionApplicationInsertGQLModel:
    applicant_id: typing.Optional[IDType] = None
    applied_date: typing.Optional[datetime.datetime] = None
    accepted: typing.Optional[bool] = None
    accepted_at: typing.Optional[datetime.datetime] = None
    acceptedby_id: typing.Optional[IDType] = None
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
    process_id: typing.Optional[IDType] = strawberry.UNSET
    payment_id: typing.Optional[IDType] = strawberry.UNSET
    offer_id: typing.Optional[IDType] = strawberry.UNSET


@strawberry.input(description="Input model for deleting an admission application")
class AdmissionApplicationDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


@strawberry.input(description="Input model for submitting an admission application")
class AdmissionApplicationSubmitGQLModel:
    offer_id: IDType


@strawberry.input(description="Input model for accepting an admission application")
class AdmissionApplicationAcceptGQLModel:
    application_id: IDType


@strawberry.type(description="Admission application mutations")
class AdmissionApplicationMutation:
    @strawberry.field(
        description="Insert an admission application",
        extensions=create_insert_permissions(
            InsertError,
            AdmissionApplicationGQLModel,
            required_roles=EDITOR_ROLES
        )
    )
    async def admission_application_insert(
        self,
        info: strawberry.Info,
        application: AdmissionApplicationInsertGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, InsertError[AdmissionApplicationGQLModel]]:
        from uoishelpers.resolvers import Insert

        # Debug logging
        user = info.context.get("user", {})
        print(f"[INSERT] User: {user.get('fullname')} ({user.get('id')})")
        print(f"[INSERT] Roles: {user.get('roles', [])}")

        _normalize_applied_date(application)
        return await Insert[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=application)

    @strawberry.field(
        description="Update an admission application",
        extensions=create_update_permissions(
            UpdateError,
            AdmissionApplicationGQLModel,
            required_roles=EDITOR_ROLES
        )
    )
    async def admission_application_update(
        self,
        info: strawberry.Info,
        application: AdmissionApplicationUpdateGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, UpdateError[AdmissionApplicationGQLModel]]:
        from uoishelpers.resolvers import Insert, Update

        # Debug logging
        user = info.context.get("user", {})
        print(f"[UPDATE] User: {user.get('fullname')} ({user.get('id')})")
        print(f"[UPDATE] Roles: {user.get('roles', [])}")
        print(f"[UPDATE] Target ID: {application.id}")

        _normalize_applied_date(application)
        return await Update[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=application)

    @strawberry.field(
        description="Delete an admission application",
        extensions=create_delete_permissions(
            DeleteError,
            AdmissionApplicationGQLModel,
            required_roles=ADMIN_ROLES
        )
    )
    async def admission_application_delete(
        self,
        info: strawberry.Info,
        application: AdmissionApplicationDeleteGQLModel
    ) -> typing.Optional[DeleteError[AdmissionApplicationGQLModel]]:
        from uoishelpers.resolvers import Delete

        # Debug logging
        user = info.context.get("user", {})
        print(f"[DELETE] User: {user.get('fullname')} ({user.get('id')})")
        print(f"[DELETE] Roles: {user.get('roles', [])}")
        print(f"[DELETE] Target ID: {application.id}")

        return await Delete[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=application)

    @strawberry.field(
        description="Submit admission application for an offer",
        permission_classes=[OnlyForAuthentized]
    )
    async def admission_application_submit(
        self,
        info: strawberry.Info,
        submission: AdmissionApplicationSubmitGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, InsertError[AdmissionApplicationGQLModel]]:
        from sqlalchemy import select
        from src.DBDefinitions import AdmissionApplicantModel
        from uoishelpers.resolvers import Insert
        from .AdmissionPaymentGQLModel import AdmissionPaymentGQLModel
        from .AdmissionPaymentGQLModel import AdmissionPaymentInsertGQLModel

        user = getUserFromInfo(info=info) or {}
        user_id = user.get("id")
        if not user_id:
            return InsertError[AdmissionApplicationGQLModel](
                msg="Missing authenticated user id",
                code="6d927b14-2b13-4ef1-9f9c-9edb0c0c2c5e",
                location="admissionApplicationSubmit",
                _input=submission
            )

        applicant_loader = getLoadersFromInfo(info).AdmissionApplicantModel
        stmt = select(AdmissionApplicantModel.id).where(
            AdmissionApplicantModel.applicant_user_id == user_id
        )
        result = await applicant_loader.session.execute(stmt)
        applicant_id = result.scalars().first()
        if applicant_id is None:
            return InsertError[AdmissionApplicationGQLModel](
                msg="Applicant profile not found for current user",
                code="3b6d7b7b-5b1d-4d11-9ec8-0e3e4a1d4b6a",
                location="admissionApplicationSubmit",
                _input=submission
            )

        offer_loader = getLoadersFromInfo(info).AdmissionOfferModel
        offer = await offer_loader.load(submission.offer_id)
        if offer is None:
            return InsertError[AdmissionApplicationGQLModel](
                msg="Admission offer not found",
                code="ed0c4b3c-0b4b-4c31-9f19-6f1b1e3d4d2a",
                location="admissionApplicationSubmit",
                _input=submission
            )

        def _to_naive(value: typing.Optional[datetime.datetime]) -> typing.Optional[datetime.datetime]:
            if value is None:
                return None
            if value.tzinfo is not None and value.utcoffset() is not None:
                return value.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            return value

        now = datetime.datetime.now()
        start_date = _to_naive(getattr(offer, "application_start_date", None))
        end_date = _to_naive(getattr(offer, "application_end_date", None))
        if start_date and now < start_date:
            return InsertError[AdmissionApplicationGQLModel](
                msg="Application period has not started yet",
                code="5f4c1c1d-9c2a-4c0d-9b0e-3f6f9b7d2a11",
                location="admissionApplicationSubmit",
                _input=submission
            )
        if end_date and now > end_date:
            return InsertError[AdmissionApplicationGQLModel](
                msg="Application period has ended",
                code="8b0f2d2f-6a3c-4b1e-9a6c-1e2f3a4b5c6d",
                location="admissionApplicationSubmit",
                _input=submission
            )

        app_loader = getLoadersFromInfo(info).AdmissionApplicationModel
        stmt = select(app_loader.dbModel.id).where(
            app_loader.dbModel.applicant_id == applicant_id,
            app_loader.dbModel.offer_id == submission.offer_id
        )
        existing = await app_loader.session.execute(stmt)
        if existing.scalars().first() is not None:
            return InsertError[AdmissionApplicationGQLModel](
                msg="Application already exists for this offer",
                code="b8f0f1a1-2c3d-4e5f-8a9b-0c1d2e3f4a5b",
                location="admissionApplicationSubmit",
                _input=submission
            )

        payment_info_loader = getLoadersFromInfo(info).AdmissionPaymentInfoModel
        payment_info = None
        if offer.payment_info_id is not None:
            payment_info = await payment_info_loader.load(offer.payment_info_id)
        if payment_info is None:
            return InsertError[AdmissionApplicationGQLModel](
                msg="Payment info not found for offer",
                code="f12a7f43-1a9e-4d1e-bd8d-3f2d0f0a9c1e",
                location="admissionApplicationSubmit",
                _input=submission
            )

        payment = AdmissionPaymentInsertGQLModel(
            required_amount=payment_info.required_amount,
            paid_at=None,
            bank_statement_id=None
        )
        payment_row = await Insert[AdmissionPaymentGQLModel].DoItSafeWay(info=info, entity=payment)
        if isinstance(payment_row, InsertError):
            return payment_row

        application = AdmissionApplicationInsertGQLModel(
            applicant_id=applicant_id,
            applied_date=now,
            payment_id=payment_row.id,
            offer_id=submission.offer_id,
        )
        application.accepted = False
        application.accepted_at = None
        application.acceptedby_id = None
        _normalize_applied_date(application)
        return await Insert[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=application)

    @strawberry.field(
        description="Accept admission application by study office",
        permission_classes=[OnlyForAuthentized]
    )
    async def admission_application_accept(
        self,
        info: strawberry.Info,
        acceptance: AdmissionApplicationAcceptGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, UpdateError[AdmissionApplicationGQLModel]]:
        from sqlalchemy import select
        from uoishelpers.resolvers import Insert, Update
        from src.DBDefinitions import AdmissionApplicationModel
        from .AdmissionProcessGQLModel import AdmissionProcessGQLModel
        from .AdmissionProcessGQLModel import AdmissionProcessInsertGQLModel

        user = getUserFromInfo(info=info) or {}
        user_id = user.get("id")
        if not user_id:
            return UpdateError[AdmissionApplicationGQLModel](
                msg="Missing authenticated user id",
                code="7bb5a2f8-7a32-4b12-9c85-9c7e1a2a6f5b",
                location="admissionApplicationAccept",
                _input=acceptance
            )

        app_loader = getLoadersFromInfo(info).AdmissionApplicationModel
        stmt = select(AdmissionApplicationModel).where(AdmissionApplicationModel.id == acceptance.application_id)
        result = await app_loader.session.execute(stmt)
        db_row = result.scalars().first()
        if db_row is None:
            return UpdateError[AdmissionApplicationGQLModel](
                msg="Admission application not found",
                code="1d6b3a0e-0f2f-4d21-8e3f-7a0b0b1d4c2f",
                location="admissionApplicationAccept",
                _input=acceptance
            )

        process = AdmissionProcessInsertGQLModel(payment_id=db_row.payment_id)
        process_row = await Insert[AdmissionProcessGQLModel].DoItSafeWay(info=info, entity=process)
        if isinstance(process_row, InsertError):
            return UpdateError[AdmissionApplicationGQLModel](
                msg=process_row.msg,
                code=process_row.code,
                location="admissionApplicationAccept",
                _input=acceptance
            )

        update = AdmissionApplicationUpdateGQLModel(
            id=db_row.id,
            lastchange=db_row.lastchange,
            process_id=process_row.id,
            accepted=True,
            accepted_at=datetime.datetime.now(),
            acceptedby_id=user_id,
        )
        _normalize_applied_date(update)
        return await Update[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=update)
