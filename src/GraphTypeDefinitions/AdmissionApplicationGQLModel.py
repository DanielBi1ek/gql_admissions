import typing
import datetime
import strawberry
import uuid as uuid_module

from uoishelpers.resolvers import getLoadersFromInfo, createInputs2, ScalarResolver
from uoishelpers.resolvers import getUserFromInfo

from .BaseGQLModel import BaseGQLModel, IDType
from .admission_permissions import (
    ADMISSION_READ_PERMISSION, ADMISSION_ADMIN_PERMISSION, ADMISSION_USER_PERMISSION,
    admission_field, get_admission_entity_by_id, get_admission_entities_page,
    is_admissions_admin
)
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

    # All fields now use centralized permission system - no more repetitive permission_classes!
    applicant_id: typing.Optional[IDType] = admission_field(
        default=None,
        description="applicant reference"
    )
    applied_date: typing.Optional[datetime.datetime] = admission_field(
        default=None,
        description="application date"
    )
    accepted: typing.Optional[bool] = admission_field(
        default=None,
        description="application accepted by study office"
    )
    accepted_at: typing.Optional[datetime.datetime] = admission_field(
        default=None,
        description="acceptance date"
    )
    acceptedby_id: typing.Optional[IDType] = admission_field(
        default=None,
        description="user who accepted application"
    )
    withdrawn: typing.Optional[bool] = admission_field(
        default=None,
        description="application withdrawn by applicant"
    )
    withdrawn_at: typing.Optional[datetime.datetime] = admission_field(
        default=None,
        description="withdrawal date"
    )
    withdrawnby_id: typing.Optional[IDType] = admission_field(
        default=None,
        description="user who withdrew application"
    )
    process_id: typing.Optional[IDType] = admission_field(
        default=None,
        description="admission process reference"
    )
    payment_id: typing.Optional[IDType] = admission_field(
        default=None,
        description="admission payment reference"
    )
    offer_id: typing.Optional[IDType] = admission_field(
        default=None,
        description="admission offer reference"
    )

    process: typing.Optional["AdmissionProcessGQLModel"] = admission_field(
        description="related admission process",
        resolver=ScalarResolver["AdmissionProcessGQLModel"](fkey_field_name="process_id")
    )
    payment: typing.Optional["AdmissionPaymentGQLModel"] = admission_field(
        description="related admission payment",
        resolver=ScalarResolver["AdmissionPaymentGQLModel"](fkey_field_name="payment_id")
    )
    offer: typing.Optional["AdmissionOfferGQLModel"] = admission_field(
        description="related admission offer",
        resolver=ScalarResolver["AdmissionOfferGQLModel"](fkey_field_name="offer_id")
    )

    applicant: typing.Optional["AdmissionApplicantGQLModel"] = admission_field(
        description="applicant details",
        resolver=ScalarResolver["AdmissionApplicantGQLModel"](fkey_field_name="applicant_id")
    )


@strawberry.type(description="Admission application queries")
class AdmissionApplicationQuery:
    @strawberry.field(
        description="get admission application by id",
        permission_classes=ADMISSION_READ_PERMISSION
    )
    async def admission_application_by_id(
        self,
        info: strawberry.Info,
        id: IDType,
    ) -> typing.Optional[AdmissionApplicationGQLModel]:
        user = getUserFromInfo(info=info) or {}
        if is_admissions_admin(user):
            return await AdmissionApplicationGQLModel.load_with_loader(info=info, id=id)

        user_id = user.get("id")
        if not user_id:
            return None

        # Load the application using the loader directly
        loader = AdmissionApplicationGQLModel.getLoader(info=info)
        _id = id if isinstance(id, IDType) else IDType(id)
        db_row = await loader.load(_id)

        if db_row is None:
            return None

        # Now check ownership through the applicant
        applicant_loader = getLoadersFromInfo(info).AdmissionApplicantModel
        applicant = await applicant_loader.load(db_row.applicant_id)
        if applicant is None:
            return None

        # Compare as strings to handle any UUID type mismatches
        db_applicant_user_id = str(applicant.applicant_user_id) if applicant.applicant_user_id else None
        request_user_id = str(user_id)

        if db_applicant_user_id != request_user_id:
            return None

        return AdmissionApplicationGQLModel.from_dataclass(db_row)

    @strawberry.field(
        description="page of admission applications",
        permission_classes=ADMISSION_READ_PERMISSION
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

        # Convert string user_id to UUID for proper comparison
        try:
            user_id_uuid = uuid_module.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, TypeError):
            return []

        applicant_stmt = select(AdmissionApplicantModel.id).where(
            AdmissionApplicantModel.applicant_user_id == user_id_uuid
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


@strawberry.input(description="Input model for deleting an admission application")
class AdmissionApplicationDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


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
        permission_classes=ADMISSION_USER_PERMISSION
    )
    async def admission_application_insert(
        self,
        info: strawberry.Info,
        application: AdmissionApplicationInsertGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, InsertError[AdmissionApplicationGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Insert

        user = getUserFromInfo(info=info)
        if not user:
            return InsertError[AdmissionApplicationGQLModel](
                msg="User not authenticated",
                entity=application
            )

        # Auto-set the applicant_id to the current user if not provided
        if application.applicant_id is None:
            # Find or create applicant record for this user
            loader = getLoadersFromInfo(info).AdmissionApplicantModel
            from sqlalchemy import select
            from src.DBDefinitions import AdmissionApplicantModel

            applicant_stmt = select(AdmissionApplicantModel.id).where(
                AdmissionApplicantModel.applicant_user_id == user["id"]
            )
            result = await loader.session.execute(applicant_stmt)
            applicant_id = result.scalars().first()

            if applicant_id is None:
                # Get user info for auto-filling
                firstname = user.get("name", "") or user.get("firstname", "")
                lastname = user.get("surname", "") or user.get("lastname", "")
                email = user.get("email", "")

                # If missing critical info, try to fetch from gql_ug
                if not firstname or not lastname or not email:
                    from uoishelpers.resolvers import getUgClientFromInfo
                    ug_client = getUgClientFromInfo(info)
                    me_response = await ug_client(
                        query="""
                        query {
                          me {
                            id
                            name
                            surname
                            email
                          }
                        }"""
                    )
                    me_data = (me_response or {}).get("data", {}).get("me", {}) or {}
                    firstname = firstname or me_data.get("name", "")
                    lastname = lastname or me_data.get("surname", "")
                    email = email or me_data.get("email", "")

                # Create new applicant record
                from src.DBDefinitions import AdmissionApplicantModel
                new_applicant = AdmissionApplicantModel(
                    id=None,  # Will be auto-generated
                    applicant_user_id=user["id"],
                    firstname=firstname,
                    lastname=lastname,
                    email=email,
                    street="",  # User can update this later
                    house_number="",
                    city="",
                    phone_number="",
                    databox_number="",
                    createdby_id=user["id"],
                    changedby_id=user["id"]
                )
                loader.session.add(new_applicant)
                await loader.session.commit()
                applicant_id = new_applicant.id

            application.applicant_id = applicant_id
        else:
            # Verify user owns the specified applicant
            if not is_admissions_admin(user):
                loader = getLoadersFromInfo(info).AdmissionApplicantModel
                from sqlalchemy import select
                from src.DBDefinitions import AdmissionApplicantModel

                applicant_stmt = select(AdmissionApplicantModel.applicant_user_id).where(
                    AdmissionApplicantModel.id == application.applicant_id
                )
                result = await loader.session.execute(applicant_stmt)
                applicant_user_id = result.scalars().first()

                if applicant_user_id != user["id"]:
                    return InsertError[AdmissionApplicationGQLModel](
                        msg="You can only create applications for yourself",
                        entity=application
                    )

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
        permission_classes=ADMISSION_USER_PERMISSION
    )
    async def admission_application_update(
        self,
        info: strawberry.Info,
        application: AdmissionApplicationUpdateGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, UpdateError[AdmissionApplicationGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Update

        user = getUserFromInfo(info=info)
        if not user:
            return UpdateError[AdmissionApplicationGQLModel](
                msg="User not authenticated",
                entity=application
            )

        # Check ownership unless user is admin
        if not is_admissions_admin(user):
            loader = getLoadersFromInfo(info).AdmissionApplicationModel
            from sqlalchemy import select
            from src.DBDefinitions import AdmissionApplicationModel, AdmissionApplicantModel

            # Check if user owns the application through the applicant
            ownership_stmt = select(AdmissionApplicantModel.applicant_user_id).join(
                AdmissionApplicationModel,
                AdmissionApplicationModel.applicant_id == AdmissionApplicantModel.id
            ).where(AdmissionApplicationModel.id == application.id)

            result = await loader.session.execute(ownership_stmt)
            owner_user_id = result.scalars().first()

            if owner_user_id != user["id"]:
                return UpdateError[AdmissionApplicationGQLModel](
                    msg="You can only update your own applications",
                    entity=application
                )

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
        permission_classes=ADMISSION_READ_PERMISSION
    )
    async def admission_application_submit(
        self,
        info: strawberry.Info,
        submission: AdmissionApplicationSubmitGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, InsertError[AdmissionApplicationGQLModel]]:
        return await submit_application(info, submission)

    @strawberry.field(
        description="Accept admission application by study office",
        permission_classes=ADMISSION_ADMIN_PERMISSION
    )
    async def admission_application_accept(
        self,
        info: strawberry.Info,
        acceptance: AdmissionApplicationAcceptGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, UpdateError[AdmissionApplicationGQLModel]]:
        return await accept_application(info, acceptance)

    @strawberry.field(
        description="Withdraw admission application by applicant",
        permission_classes=ADMISSION_READ_PERMISSION
    )
    async def admission_application_withdraw(
        self,
        info: strawberry.Info,
        withdrawal: AdmissionApplicationWithdrawGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, UpdateError[AdmissionApplicationGQLModel]]:
        return await withdraw_application(info, withdrawal)

    @strawberry.field(
        description="Delete admission application (admin only)",
        permission_classes=ADMISSION_ADMIN_PERMISSION
    )
    async def admission_application_delete(
        self,
        info: strawberry.Info,
        application: AdmissionApplicationDeleteGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, UpdateError[AdmissionApplicationGQLModel]]:
        from uoishelpers.resolvers import Delete, DeleteError
        from .validation import build_error
        from . import error_codes as codes

        # Load the entity before deletion to get complete data for result
        loader = getLoadersFromInfo(info).AdmissionApplicationModel
        db_row = await loader.load(application.id)
        if db_row is None:
            return build_error(
                DeleteError[AdmissionApplicationGQLModel],
                msg="Application not found",
                code=codes.ERR_NOT_FOUND,
                location="admissionApplicationDelete",
                input_obj=application,
            )

        # Perform the deletion
        result = await Delete[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=application)

        # Check if deletion failed
        if isinstance(result, DeleteError):
            return result

        # Return the deleted entity data as result (convert from db_row)
        return AdmissionApplicationGQLModel.from_dataclass(db_row)
