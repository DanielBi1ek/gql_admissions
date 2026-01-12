from __future__ import annotations

import datetime
import typing

from uoishelpers.resolvers import Insert, InsertError, Update, UpdateError, getLoadersFromInfo, getUserFromInfo

from src.GraphTypeDefinitions import error_codes as codes
from src.GraphTypeDefinitions.db_errors import integrity_error_to_error
from src.GraphTypeDefinitions.validation import build_error, normalize_datetime_field, to_naive_datetime


async def submit_application(
    info: typing.Any,
    submission: typing.Any,
) -> typing.Any:
    from sqlalchemy import select
    from src.DBDefinitions import AdmissionApplicantModel
    from src.GraphTypeDefinitions.AdmissionPaymentGQLModel import (
        AdmissionPaymentGQLModel,
        AdmissionPaymentInsertGQLModel,
    )
    from src.GraphTypeDefinitions.AdmissionApplicationGQLModel import (
        AdmissionApplicationGQLModel,
        AdmissionApplicationInsertGQLModel,
    )

    user = getUserFromInfo(info=info) or {}
    user_id = user.get("id")
    if not user_id:
        return build_error(
            InsertError[AdmissionApplicationGQLModel],
            msg="Missing authenticated user id",
            code=codes.ERR_SUBMIT_USER_MISSING,
            location="admissionApplicationSubmit",
            input_obj=submission,
        )

    applicant_loader = getLoadersFromInfo(info).AdmissionApplicantModel
    stmt = select(AdmissionApplicantModel.id).where(
        AdmissionApplicantModel.applicant_user_id == user_id
    )
    result = await applicant_loader.session.execute(stmt)
    applicant_id = result.scalars().first()
    if applicant_id is None:
        return build_error(
            InsertError[AdmissionApplicationGQLModel],
            msg="Applicant profile not found for current user",
            code=codes.ERR_APPLICANT_PROFILE_NOT_FOUND,
            location="admissionApplicationSubmit",
            input_obj=submission,
        )

    offer_loader = getLoadersFromInfo(info).AdmissionOfferModel
    offer = await offer_loader.load(submission.offer_id)
    if offer is None:
        return build_error(
            InsertError[AdmissionApplicationGQLModel],
            msg="Admission offer not found",
            code=codes.ERR_OFFER_NOT_FOUND,
            location="admissionApplicationSubmit",
            input_obj=submission,
        )

    now = datetime.datetime.utcnow()
    start_date = to_naive_datetime(getattr(offer, "application_start_date", None))
    end_date = to_naive_datetime(getattr(offer, "application_end_date", None))
    if start_date and now < start_date:
        return build_error(
            InsertError[AdmissionApplicationGQLModel],
            msg="Application period has not started yet",
            code=codes.ERR_OFFER_NOT_STARTED,
            location="admissionApplicationSubmit",
            input_obj=submission,
        )
    if end_date and now > end_date:
        return build_error(
            InsertError[AdmissionApplicationGQLModel],
            msg="Application period has ended",
            code=codes.ERR_OFFER_ENDED,
            location="admissionApplicationSubmit",
            input_obj=submission,
        )

    app_loader = getLoadersFromInfo(info).AdmissionApplicationModel
    stmt = select(app_loader.dbModel.id).where(
        app_loader.dbModel.applicant_id == applicant_id,
        app_loader.dbModel.offer_id == submission.offer_id
    )
    existing = await app_loader.session.execute(stmt)
    if existing.scalars().first() is not None:
        return build_error(
            InsertError[AdmissionApplicationGQLModel],
            msg="Application already exists for this offer",
            code=codes.ERR_APPLICATION_EXISTS,
            location="admissionApplicationSubmit",
            input_obj=submission,
        )

    payment_info_loader = getLoadersFromInfo(info).AdmissionPaymentInfoModel
    payment_info = None
    if offer.payment_info_id is not None:
        payment_info = await payment_info_loader.load(offer.payment_info_id)
    if payment_info is None:
        return build_error(
            InsertError[AdmissionApplicationGQLModel],
            msg="Payment info not found for offer",
            code=codes.ERR_OFFER_PAYMENT_INFO_NOT_FOUND,
            location="admissionApplicationSubmit",
            input_obj=submission,
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
            normalize_datetime_field(application, "applied_date")
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


async def accept_application(
    info: typing.Any,
    acceptance: typing.Any,
) -> typing.Any:
    from sqlalchemy import select
    from src.DBDefinitions import AdmissionApplicationModel
    from src.GraphTypeDefinitions.AdmissionApplicationGQLModel import (
        AdmissionApplicationGQLModel,
        AdmissionApplicationUpdateGQLModel,
    )
    from src.GraphTypeDefinitions.AdmissionProcessGQLModel import (
        AdmissionProcessGQLModel,
        AdmissionProcessInsertGQLModel,
    )

    user = getUserFromInfo(info=info) or {}
    user_id = user.get("id")
    if not user_id:
        return build_error(
            UpdateError[AdmissionApplicationGQLModel],
            msg="Missing authenticated user id",
            code=codes.ERR_ACCEPT_USER_MISSING,
            location="admissionApplicationAccept",
            input_obj=acceptance,
        )

    app_loader = getLoadersFromInfo(info).AdmissionApplicationModel
    stmt = select(AdmissionApplicationModel).where(AdmissionApplicationModel.id == acceptance.application_id)
    result = await app_loader.session.execute(stmt)
    db_row = result.scalars().first()
    if db_row is None:
        return build_error(
            UpdateError[AdmissionApplicationGQLModel],
            msg="Admission application not found",
            code=codes.ERR_APPLICATION_NOT_FOUND,
            location="admissionApplicationAccept",
            input_obj=acceptance,
        )
    if getattr(db_row, "accepted", False):
        return build_error(
            UpdateError[AdmissionApplicationGQLModel],
            msg="Application already accepted",
            code=codes.ERR_APPLICATION_ALREADY_ACCEPTED,
            location="admissionApplicationAccept",
            input_obj=acceptance,
        )
    if getattr(db_row, "withdrawn", False):
        return build_error(
            UpdateError[AdmissionApplicationGQLModel],
            msg="Cannot accept a withdrawn application",
            code=codes.ERR_APPLICATION_WITHDRAWN,
            location="admissionApplicationAccept",
            input_obj=acceptance,
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
            updated = await Update[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=update)
            if isinstance(updated, UpdateError):
                raise _AbortTransaction(updated)
            return updated
    except _AbortTransaction as exc:
        return exc.result


async def withdraw_application(
    info: typing.Any,
    withdrawal: typing.Any,
) -> typing.Any:
    from sqlalchemy import select
    from src.DBDefinitions import AdmissionApplicationModel, AdmissionApplicantModel
    from src.GraphTypeDefinitions.AdmissionApplicationGQLModel import (
        AdmissionApplicationGQLModel,
        AdmissionApplicationUpdateGQLModel,
    )

    user = getUserFromInfo(info=info) or {}
    user_id = user.get("id")
    if not user_id:
        return build_error(
            UpdateError[AdmissionApplicationGQLModel],
            msg="Missing authenticated user id",
            code=codes.ERR_WITHDRAW_USER_MISSING,
            location="admissionApplicationWithdraw",
            input_obj=withdrawal,
        )

    app_loader = getLoadersFromInfo(info).AdmissionApplicationModel
    stmt = select(AdmissionApplicationModel).where(AdmissionApplicationModel.id == withdrawal.application_id)
    result = await app_loader.session.execute(stmt)
    db_row = result.scalars().first()
    if db_row is None:
        return build_error(
            UpdateError[AdmissionApplicationGQLModel],
            msg="Admission application not found",
            code=codes.ERR_WITHDRAW_APPLICATION_NOT_FOUND,
            location="admissionApplicationWithdraw",
            input_obj=withdrawal,
        )

    applicant_loader = getLoadersFromInfo(info).AdmissionApplicantModel
    stmt = select(AdmissionApplicantModel.id).where(
        AdmissionApplicantModel.id == db_row.applicant_id,
        AdmissionApplicantModel.applicant_user_id == user_id
    )
    applicant = await applicant_loader.session.execute(stmt)
    if applicant.scalars().first() is None:
        return build_error(
            UpdateError[AdmissionApplicationGQLModel],
            msg="Cannot withdraw application for another applicant",
            code=codes.ERR_WITHDRAW_NOT_OWNER,
            location="admissionApplicationWithdraw",
            input_obj=withdrawal,
        )

    update = AdmissionApplicationUpdateGQLModel(
        id=db_row.id,
        lastchange=db_row.lastchange,
        withdrawn=True,
        withdrawn_at=datetime.datetime.utcnow(),
        withdrawnby_id=user_id,
    )
    return await Update[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=update)
