import typing

from sqlalchemy.exc import IntegrityError


def _detail_from_exc(exc: Exception) -> str:
    detail = ""
    if isinstance(exc, IntegrityError):
        detail = str(exc.orig) if getattr(exc, "orig", None) is not None else str(exc)
    else:
        detail = str(exc)
    return detail


def _match(detail: str, patterns: typing.Iterable[str]) -> bool:
    return any(pattern in detail for pattern in patterns)


def integrity_error_to_error(exc: Exception, error_cls, location: str, input_obj):
    detail = _detail_from_exc(exc)
    constraint_name = None
    if isinstance(exc, IntegrityError):
        orig = getattr(exc, "orig", None)
        if orig is not None:
            constraint_name = getattr(orig, "constraint_name", None)
            if constraint_name is None:
                diag = getattr(orig, "diag", None)
                constraint_name = getattr(diag, "constraint_name", None) if diag is not None else None

    mappings = [
        (
            ["uq_admission_offers_program_id", "UNIQUE constraint failed: admission_offers.program_id"],
            "Offer already exists for this study program",
            "c6f27c8c-33d8-4cd0-a76a-5eb3f4a59262",
        ),
        (
            [
                "uq_admission_applications_applicant_offer",
                "UNIQUE constraint failed: admission_applications.applicant_id, admission_applications.offer_id",
            ],
            "Application already exists for this offer",
            "b8f0f1a1-2c3d-4e5f-8a9b-0c1d2e3f4a5b",
        ),
        (
            ["UNIQUE constraint failed: admission_applicants.applicant_user_id"],
            "Applicant profile already exists for this user",
            "e7f2f3c3-0e6d-4a9a-8c1a-5c7a621f8a1c",
        ),
        (
            [
                "uq_admission_bank_accounts_identity",
                "UNIQUE constraint failed: admission_bank_accounts.account_prefix, admission_bank_accounts.account_number, admission_bank_accounts.bank_code",
            ],
            "Bank account already exists",
            "f4b8a7c1-2d9b-4c1a-8a51-6d71b2f0c1e9",
        ),
        (
            [
                "ck_admission_payment_infos_required_amount_gt0",
                "CHECK constraint failed: ck_admission_payment_infos_required_amount_gt0",
            ],
            "Required amount must be greater than 0",
            "f2a1d19b-0e5f-4c2b-b2e9-9f40b81d3bd5",
        ),
        (
            [
                "ck_admission_payments_required_amount_gt0",
                "CHECK constraint failed: ck_admission_payments_required_amount_gt0",
            ],
            "Required amount must be greater than 0",
            "f2a1d19b-0e5f-4c2b-b2e9-9f40b81d3bd5",
        ),
        (
            ["NOT NULL constraint failed", "null value in column"],
            "Missing required value",
            "a3c2a8f9-3f19-4e88-a5a0-1a7a4f6f0f8d",
        ),
        (
            ["FOREIGN KEY constraint failed", "violates foreign key constraint"],
            "Referenced entity not found",
            "d0c5b7a4-0f2a-45a8-8c31-6ab1ef3a7c9a",
        ),
    ]

    for patterns, msg, code in mappings:
        if constraint_name and constraint_name in patterns:
            return error_cls(msg=msg, code=code, location=location, _input=input_obj)
        if _match(detail, patterns):
            return error_cls(msg=msg, code=code, location=location, _input=input_obj)

    return error_cls(
        msg="Database constraint violation",
        code="c9f3a2e7-1d8a-4f66-9e64-3f5c1a2b4c6d",
        location=location,
        _input=input_obj
    )
