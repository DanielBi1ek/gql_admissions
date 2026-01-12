import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, createInputs2, getUserFromInfo
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType
from .admission_permissions import AdmissionsAdminPermission, is_admissions_admin
from .pagination import resolve_page
from .validation import build_error
from . import error_codes as codes


@createInputs2
class AdmissionApplicantInputFilter:
    id: IDType
    applicant_user_id: IDType
    firstname: str
    lastname: str
    street: str
    house_number: str
    city: str
    phone_number: str
    email: str
    databox_number: str


@strawberry.federation.type(keys=["id"], description="Applicant personal data record")
class AdmissionApplicantGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).AdmissionApplicantModel

    applicant_user_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="applicant user reference",
        permission_classes=[OnlyForAuthentized]
    )
    firstname: typing.Optional[str] = strawberry.field(
        default=None,
        description="first name",
        permission_classes=[OnlyForAuthentized]
    )
    lastname: typing.Optional[str] = strawberry.field(
        default=None,
        description="last name",
        permission_classes=[OnlyForAuthentized]
    )
    street: typing.Optional[str] = strawberry.field(
        default=None,
        description="street",
        permission_classes=[OnlyForAuthentized]
    )
    house_number: typing.Optional[str] = strawberry.field(
        default=None,
        description="house number",
        permission_classes=[OnlyForAuthentized]
    )
    city: typing.Optional[str] = strawberry.field(
        default=None,
        description="city",
        permission_classes=[OnlyForAuthentized]
    )
    phone_number: typing.Optional[str] = strawberry.field(
        default=None,
        description="phone number",
        permission_classes=[OnlyForAuthentized]
    )
    email: typing.Optional[str] = strawberry.field(
        default=None,
        description="email address",
        permission_classes=[OnlyForAuthentized]
    )
    databox_number: typing.Optional[str] = strawberry.field(
        default=None,
        description="databox number",
        permission_classes=[OnlyForAuthentized]
    )


@strawberry.type(description="Admission applicant queries")
class AdmissionApplicantQuery:
    @strawberry.field(
        description="get admission applicant by id",
        permission_classes=[OnlyForAuthentized]
    )
    async def admission_applicant_by_id(
        self,
        info: strawberry.Info,
        id: IDType
    ) -> typing.Optional[AdmissionApplicantGQLModel]:
        from sqlalchemy import select

        user = getUserFromInfo(info=info) or {}
        if is_admissions_admin(user):
            return await AdmissionApplicantGQLModel.load_with_loader(info=info, id=id)

        user_id = user.get("id")
        if not user_id:
            return None

        loader = AdmissionApplicantGQLModel.getLoader(info=info)
        stmt = select(loader.dbModel.id).where(
            loader.dbModel.id == id,
            loader.dbModel.applicant_user_id == user_id
        )
        result = await loader.session.execute(stmt)
        row_id = result.scalars().first()
        if row_id is None:
            return None
        db_row = await loader.load(row_id)
        return None if db_row is None else AdmissionApplicantGQLModel.from_dataclass(db_row)

    @strawberry.field(
        description="page of admission applicants",
        permission_classes=[OnlyForAuthentized]
    )
    async def admission_applicant_page(
        self,
        info: strawberry.Info,
        where: typing.Optional[AdmissionApplicantInputFilter] = None,
        skip: typing.Optional[int] = 0,
        limit: typing.Optional[int] = 10,
        orderby: typing.Optional[str] = None,
        desc: typing.Optional[bool] = None,
        offset: typing.Optional[int] = None,
    ) -> typing.List[AdmissionApplicantGQLModel]:
        from sqlalchemy import select

        user = getUserFromInfo(info=info) or {}
        if offset is not None:
            skip = offset
        if is_admissions_admin(user):
            return await resolve_page(
                info,
                AdmissionApplicantGQLModel,
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

        loader = AdmissionApplicantGQLModel.getLoader(info=info)
        stmt = select(loader.dbModel).where(loader.dbModel.applicant_user_id == user_id)
        result = await loader.session.execute(stmt)
        db_row = result.scalars().first()
        if db_row is None:
            return []
        if skip and skip > 0:
            return []
        if limit is not None and limit <= 0:
            return []
        return [AdmissionApplicantGQLModel.from_dataclass(db_row)]


from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating an admission applicant")
class AdmissionApplicantInsertGQLModel:
    applicant_user_id: typing.Optional[IDType] = None
    firstname: typing.Optional[str] = None
    lastname: typing.Optional[str] = None
    street: typing.Optional[str] = None
    house_number: typing.Optional[str] = None
    city: typing.Optional[str] = None
    phone_number: typing.Optional[str] = None
    email: typing.Optional[str] = None
    databox_number: typing.Optional[str] = None


@strawberry.input(description="Input model for updating an admission applicant")
class AdmissionApplicantUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    applicant_user_id: typing.Optional[IDType] = strawberry.UNSET
    firstname: typing.Optional[str] = strawberry.UNSET
    lastname: typing.Optional[str] = strawberry.UNSET
    street: typing.Optional[str] = strawberry.UNSET
    house_number: typing.Optional[str] = strawberry.UNSET
    city: typing.Optional[str] = strawberry.UNSET
    phone_number: typing.Optional[str] = strawberry.UNSET
    email: typing.Optional[str] = strawberry.UNSET
    databox_number: typing.Optional[str] = strawberry.UNSET


@strawberry.input(description="Input model for deleting an admission applicant")
class AdmissionApplicantDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


@strawberry.input(description="Input model for initializing an admission applicant profile")
class AdmissionApplicantInitGQLModel:
    street: str
    house_number: str
    city: str
    phone_number: str
    email: str
    databox_number: typing.Optional[str] = None


@strawberry.type(description="Admission applicant mutations")
class AdmissionApplicantMutation:
    @strawberry.mutation(
        description="Initialize admission applicant profile for the current user",
        permission_classes=[OnlyForAuthentized]
    )
    async def admission_applicant_init(
        self,
        info: strawberry.Info,
        applicant: AdmissionApplicantInitGQLModel
    ) -> typing.Union[AdmissionApplicantGQLModel, InsertError[AdmissionApplicantGQLModel]]:
        from sqlalchemy import select
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Insert, getUserFromInfo, getUgClientFromInfo
        from src.DBDefinitions import AdmissionApplicantModel
        from .db_errors import integrity_error_to_error

        user = getUserFromInfo(info=info) or {}
        user_id = user.get("id")
        firstname = user.get("name") or user.get("firstname")
        lastname = user.get("surname") or user.get("lastname")
        if not user_id:
            return build_error(
                InsertError[AdmissionApplicantGQLModel],
                msg="Missing authenticated user id",
                code=codes.ERR_AUTH_USER_MISSING,
                location="admissionApplicantInit",
                input_obj=applicant,
            )
        if not firstname or not lastname:
            ug_client = getUgClientFromInfo(info)
            me_response = await ug_client(
                query="""
                query {
                  me {
                    id
                    name
                    surname
                  }
                }"""
            )
            me_data = (me_response or {}).get("data", {}).get("me", {}) or {}
            firstname = firstname or me_data.get("name")
            lastname = lastname or me_data.get("surname")
        if not firstname or not lastname:
            return build_error(
                InsertError[AdmissionApplicantGQLModel],
                msg="Missing user name or surname in context",
                code=codes.ERR_AUTH_USER_NAME_MISSING,
                location="admissionApplicantInit",
                input_obj=applicant,
            )

        loader = AdmissionApplicantGQLModel.getLoader(info=info)
        stmt = select(AdmissionApplicantModel.id).where(
            AdmissionApplicantModel.applicant_user_id == user_id
        )
        result = await loader.session.execute(stmt)
        existing_id = result.scalars().first()
        if existing_id is not None:
            return build_error(
                InsertError[AdmissionApplicantGQLModel],
                msg="Applicant profile already exists for this user",
                code=codes.ERR_APPLICANT_EXISTS,
                location="admissionApplicantInit",
                input_obj=applicant,
            )

        applicant_data = AdmissionApplicantInsertGQLModel(
            applicant_user_id=user_id,
            firstname=firstname,
            lastname=lastname,
            street=applicant.street,
            house_number=applicant.house_number,
            city=applicant.city,
            phone_number=applicant.phone_number,
            email=applicant.email,
            databox_number=applicant.databox_number,
        )
        try:
            return await Insert[AdmissionApplicantGQLModel].DoItSafeWay(info=info, entity=applicant_data)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                InsertError[AdmissionApplicantGQLModel],
                "admissionApplicantInit",
                applicant
            )

    @strawberry.mutation(
        description="Insert admission applicant",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission],
    )
    async def admission_applicant_insert(
        self,
        info: strawberry.Info,
        applicant: AdmissionApplicantInsertGQLModel
    ) -> typing.Union[AdmissionApplicantGQLModel, InsertError[AdmissionApplicantGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Insert
        from .db_errors import integrity_error_to_error

        if applicant.applicant_user_id is None:
            return build_error(
                InsertError[AdmissionApplicantGQLModel],
                msg="Missing required value",
                code=codes.ERR_MISSING_REQUIRED,
                location="admissionApplicantInsert",
                input_obj=applicant,
            )
        if any(
            value is None
            for value in (
                applicant.firstname,
                applicant.lastname,
                applicant.street,
                applicant.house_number,
                applicant.city,
                applicant.phone_number,
                applicant.email,
            )
        ):
            return build_error(
                InsertError[AdmissionApplicantGQLModel],
                msg="Missing required value",
                code=codes.ERR_MISSING_REQUIRED,
                location="admissionApplicantInsert",
                input_obj=applicant,
            )

        try:
            return await Insert[AdmissionApplicantGQLModel].DoItSafeWay(info=info, entity=applicant)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                InsertError[AdmissionApplicantGQLModel],
                "admissionApplicantInsert",
                applicant
            )

    @strawberry.mutation(
        description="Update admission applicant",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[UpdateError, AdmissionApplicantGQLModel]()]
    )
    async def admission_applicant_update(
        self,
        info: strawberry.Info,
        applicant: AdmissionApplicantUpdateGQLModel,
        db_row: typing.Any
    ) -> typing.Union[AdmissionApplicantGQLModel, UpdateError[AdmissionApplicantGQLModel]]:
        from sqlalchemy import select
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Update
        from src.DBDefinitions import AdmissionApplicationModel
        from .db_errors import integrity_error_to_error

        user = getUserFromInfo(info=info) or {}
        if not is_admissions_admin(user):
            user_id = user.get("id")
            if not user_id or db_row.applicant_user_id != user_id:
                return build_error(
                    UpdateError[AdmissionApplicantGQLModel],
                    msg="You can only update your own applicant profile",
                    code=codes.ERR_APPLICANT_NOT_OWNER,
                    location="admissionApplicantUpdate",
                    input_obj=applicant,
                )

        applicant_loader = AdmissionApplicantGQLModel.getLoader(info=info)
        stmt = select(AdmissionApplicationModel.id).where(
            AdmissionApplicationModel.applicant_id == applicant.id
        )
        result = await applicant_loader.session.execute(stmt)
        if result.scalars().first() is not None:
            return build_error(
                UpdateError[AdmissionApplicantGQLModel],
                msg="Applicant cannot be updated after application submission",
                code=codes.ERR_APPLICANT_UPDATE_FORBIDDEN,
                location="admissionApplicantUpdate",
                input_obj=applicant,
            )

        try:
            return await Update[AdmissionApplicantGQLModel].DoItSafeWay(info=info, entity=applicant)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                UpdateError[AdmissionApplicantGQLModel],
                "admissionApplicantUpdate",
                applicant
            )

    @strawberry.mutation(
        description="Delete admission applicant",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[DeleteError, AdmissionApplicantGQLModel]()]
    )
    async def admission_applicant_delete(
        self,
        info: strawberry.Info,
        applicant: AdmissionApplicantDeleteGQLModel,
        db_row: typing.Any
    ) -> typing.Optional[DeleteError[AdmissionApplicantGQLModel]]:
        from sqlalchemy import select
        from uoishelpers.resolvers import Delete
        from src.DBDefinitions import AdmissionApplicationModel

        user = getUserFromInfo(info=info) or {}
        if not is_admissions_admin(user):
            user_id = user.get("id")
            if not user_id or db_row.applicant_user_id != user_id:
                return build_error(
                    DeleteError[AdmissionApplicantGQLModel],
                    msg="You can only delete your own applicant profile",
                    code=codes.ERR_APPLICANT_DELETE_NOT_OWNER,
                    location="admissionApplicantDelete",
                    input_obj=applicant,
                )

        applicant_loader = AdmissionApplicantGQLModel.getLoader(info=info)
        stmt = select(AdmissionApplicationModel.id).where(
            AdmissionApplicationModel.applicant_id == applicant.id
        )
        result = await applicant_loader.session.execute(stmt)
        if result.scalars().first() is not None:
            return build_error(
                DeleteError[AdmissionApplicantGQLModel],
                msg="Applicant cannot be deleted after application submission",
                code=codes.ERR_APPLICANT_DELETE_FORBIDDEN,
                location="admissionApplicantDelete",
                input_obj=applicant,
            )

        return await Delete[AdmissionApplicantGQLModel].DoItSafeWay(info=info, entity=applicant)
