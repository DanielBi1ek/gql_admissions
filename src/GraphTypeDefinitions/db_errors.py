import typing

from sqlalchemy.exc import IntegrityError

from . import error_codes as codes

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
            codes.ERR_OFFER_EXISTS,
        ),
        (
            [
                "uq_admission_applications_applicant_offer",
                "UNIQUE constraint failed: admission_applications.applicant_id, admission_applications.offer_id",
            ],
            "Application already exists for this offer",
            codes.ERR_APPLICATION_EXISTS,
        ),
        (
            ["UNIQUE constraint failed: admission_applicants.applicant_user_id"],
            "Applicant profile already exists for this user",
            codes.ERR_APPLICANT_EXISTS,
        ),
        (
            [
                "uq_admission_bank_accounts_identity",
                "UNIQUE constraint failed: admission_bank_accounts.account_prefix, admission_bank_accounts.account_number, admission_bank_accounts.bank_code",
            ],
            "Bank account already exists",
            codes.ERR_BANK_ACCOUNT_EXISTS,
        ),
        (
            [
                "ck_admission_payment_infos_required_amount_gt0",
                "CHECK constraint failed: ck_admission_payment_infos_required_amount_gt0",
            ],
            "Required amount must be greater than 0",
            codes.ERR_REQUIRED_POSITIVE,
        ),
        (
            [
                "ck_admission_payments_required_amount_gt0",
                "CHECK constraint failed: ck_admission_payments_required_amount_gt0",
            ],
            "Required amount must be greater than 0",
            codes.ERR_REQUIRED_POSITIVE,
        ),
        (
            ["NOT NULL constraint failed", "null value in column"],
            "Missing required value",
            codes.ERR_MISSING_REQUIRED,
        ),
        (
            ["FOREIGN KEY constraint failed", "violates foreign key constraint"],
            "Referenced entity not found",
            codes.ERR_DB_REFERENCED_NOT_FOUND,
        ),
    ]

    for patterns, msg, code in mappings:
        if constraint_name and constraint_name in patterns:
            return error_cls(msg=msg, code=code, location=location, _input=input_obj)
        if _match(detail, patterns):
            return error_cls(msg=msg, code=code, location=location, _input=input_obj)

    return error_cls(
        msg="Database constraint violation",
        code=codes.ERR_DB_CONSTRAINT_VIOLATION,
        location=location,
        _input=input_obj
    )
