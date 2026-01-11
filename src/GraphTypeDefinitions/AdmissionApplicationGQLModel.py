import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import getUserFromInfo

from .BaseGQLModel import BaseGQLModel, IDType
from .admission_permissions import AdmissionsAdminPermission
from uoishelpers.resolvers import InsertError, UpdateError
from .db_errors import integrity_error_to_error


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


def _is_admissions_admin(user: typing.Any) -> bool:
    roles = user.get("roles", []) or []
    for role in roles:
        group_id = (role.get("group") or {}).get("id")
        roletype_id = (role.get("roletype") or {}).get("id")
        if (
            group_id == AdmissionsAdminPermission.GROUP_ID
            and roletype_id == AdmissionsAdminPermission.ROLETYPE_ID
        ):
            return True
    return False


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
        if _is_admissions_admin(user):
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
        wheredict = None if where is None else strawberry.asdict(where)

        if _is_admissions_admin(user):
            rows = await loader.page(
                where=wheredict,
                skip=skip or 0,
                limit=limit,
                orderby=orderby,
                desc=desc,
            )
            return [AdmissionApplicationGQLModel.from_dataclass(row) for row in rows]

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

        rows = await loader.page(
            where=wheredict,
            skip=skip or 0,
            limit=limit,
            orderby=orderby,
            desc=desc,
            extendedfilter={"applicant_id": applicant_id},
        )
        return [AdmissionApplicationGQLModel.from_dataclass(row) for row in rows]


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

        _normalize_applied_date(application)
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

        _normalize_applied_date(application)
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

        now = datetime.datetime.utcnow()
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

        class _AbortTransaction(Exception):
            def __init__(self, result):
                super().__init__("abort transaction")
                self.result = result

        session = app_loader.session
        tx = session.begin_nested() if session.in_transaction() else session.begin()
        try:
            async with tx:
                payment = AdmissionPaymentInsertGQLModel(
                    required_amount=payment_info.required_amount,
                    paid_at=None,
                    bank_statement_id=None
                )
                try:
                    payment_row = await Insert[AdmissionPaymentGQLModel].DoItSafeWay(info=info, entity=payment)
                except Exception as exc:
                    raise _AbortTransaction(
                        integrity_error_to_error(
                            exc,
                            InsertError[AdmissionApplicationGQLModel],
                            "admissionApplicationSubmit",
                            submission
                        )
                    ) from exc
                if isinstance(payment_row, InsertError):
                    raise _AbortTransaction(payment_row)

                application = AdmissionApplicationInsertGQLModel(
                    applicant_id=applicant_id,
                    applied_date=now,
                    payment_id=payment_row.id,
                    offer_id=submission.offer_id,
                )
                application.accepted = False
                application.accepted_at = None
                application.acceptedby_id = None
                application.withdrawn = False
                application.withdrawn_at = None
                application.withdrawnby_id = None
                _normalize_applied_date(application)
                try:
                    app_row = await Insert[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=application)
                except Exception as exc:
                    raise _AbortTransaction(
                        integrity_error_to_error(
                            exc,
                            InsertError[AdmissionApplicationGQLModel],
                            "admissionApplicationSubmit",
                            submission
                        )
                    ) from exc
                if isinstance(app_row, InsertError):
                    raise _AbortTransaction(app_row)
                return app_row
        except _AbortTransaction as exc:
            return exc.result

    @strawberry.field(
        description="Accept admission application by study office",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission]
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
        if getattr(db_row, "accepted", False):
            return UpdateError[AdmissionApplicationGQLModel](
                msg="Application already accepted",
                code="9f4b7f2a-64b4-4d7b-9e60-8a2d9c1f3b72",
                location="admissionApplicationAccept",
                _input=acceptance
            )
        if getattr(db_row, "withdrawn", False):
            return UpdateError[AdmissionApplicationGQLModel](
                msg="Cannot accept a withdrawn application",
                code="c2d8f6a1-b04c-4e2c-9b3f-9e6c1c6b67d9",
                location="admissionApplicationAccept",
                _input=acceptance
            )

        class _AbortTransaction(Exception):
            def __init__(self, result):
                super().__init__("abort transaction")
                self.result = result

        session = app_loader.session
        existing_process_id = getattr(db_row, "process_id", None)
        tx = session.begin_nested() if session.in_transaction() else session.begin()
        try:
            async with tx:
                process_id = existing_process_id
                if process_id is None:
                    process = AdmissionProcessInsertGQLModel(payment_id=db_row.payment_id)
                    process_row = await Insert[AdmissionProcessGQLModel].DoItSafeWay(info=info, entity=process)
                    if isinstance(process_row, InsertError):
                        raise _AbortTransaction(
                            UpdateError[AdmissionApplicationGQLModel](
                                msg=process_row.msg,
                                code=process_row.code,
                                location="admissionApplicationAccept",
                                _input=acceptance
                            )
                        )
                    process_id = process_row.id

                update = AdmissionApplicationUpdateGQLModel(
                    id=db_row.id,
                    lastchange=db_row.lastchange,
                    process_id=process_id,
                    accepted=True,
                    accepted_at=datetime.datetime.utcnow(),
                    acceptedby_id=user_id,
                )
                _normalize_applied_date(update)
                updated = await Update[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=update)
                if isinstance(updated, UpdateError):
                    raise _AbortTransaction(updated)
                return updated
        except _AbortTransaction as exc:
            return exc.result

    @strawberry.field(
        description="Withdraw admission application by applicant",
        permission_classes=[OnlyForAuthentized]
    )
    async def admission_application_withdraw(
        self,
        info: strawberry.Info,
        withdrawal: AdmissionApplicationWithdrawGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, UpdateError[AdmissionApplicationGQLModel]]:
        from sqlalchemy import select
        from uoishelpers.resolvers import Update
        from src.DBDefinitions import AdmissionApplicationModel, AdmissionApplicantModel

        user = getUserFromInfo(info=info) or {}
        user_id = user.get("id")
        if not user_id:
            return UpdateError[AdmissionApplicationGQLModel](
                msg="Missing authenticated user id",
                code="d42c8e2c-3d01-4f52-9eb9-569b4f57a6d1",
                location="admissionApplicationWithdraw",
                _input=withdrawal
            )

        app_loader = getLoadersFromInfo(info).AdmissionApplicationModel
        stmt = select(AdmissionApplicationModel).where(AdmissionApplicationModel.id == withdrawal.application_id)
        result = await app_loader.session.execute(stmt)
        db_row = result.scalars().first()
        if db_row is None:
            return UpdateError[AdmissionApplicationGQLModel](
                msg="Admission application not found",
                code="0f5ef0d1-3b2b-49bb-9da8-1d0a0fdfdc68",
                location="admissionApplicationWithdraw",
                _input=withdrawal
            )

        applicant_loader = getLoadersFromInfo(info).AdmissionApplicantModel
        stmt = select(AdmissionApplicantModel.id).where(
            AdmissionApplicantModel.id == db_row.applicant_id,
            AdmissionApplicantModel.applicant_user_id == user_id
        )
        applicant = await applicant_loader.session.execute(stmt)
        if applicant.scalars().first() is None:
            return UpdateError[AdmissionApplicationGQLModel](
                msg="Cannot withdraw application for another applicant",
                code="b1e4b6a1-3f7b-4b83-a38d-8a5a6d5c4f12",
                location="admissionApplicationWithdraw",
                _input=withdrawal
            )

        update = AdmissionApplicationUpdateGQLModel(
            id=db_row.id,
            lastchange=db_row.lastchange,
            withdrawn=True,
            withdrawn_at=datetime.datetime.utcnow(),
            withdrawnby_id=user_id,
        )
        return await Update[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=update)
