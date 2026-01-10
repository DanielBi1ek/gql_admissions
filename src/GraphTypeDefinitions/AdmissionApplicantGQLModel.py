import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType


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
    admission_applicant_by_id: typing.Optional[AdmissionApplicantGQLModel] = strawberry.field(
        description="get admission applicant by id",
        permission_classes=[OnlyForAuthentized],
        resolver=AdmissionApplicantGQLModel.load_with_loader
    )

    admission_applicant_page: typing.List[AdmissionApplicantGQLModel] = strawberry.field(
        description="page of admission applicants",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[AdmissionApplicantGQLModel](whereType=AdmissionApplicantInputFilter)
    )


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
    applicant_user_id: typing.Optional[IDType] = None
    firstname: typing.Optional[str] = None
    lastname: typing.Optional[str] = None
    street: typing.Optional[str] = None
    house_number: typing.Optional[str] = None
    city: typing.Optional[str] = None
    phone_number: typing.Optional[str] = None
    email: typing.Optional[str] = None
    databox_number: typing.Optional[str] = None


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
        from uoishelpers.resolvers import Insert, getUserFromInfo, getUgClientFromInfo
        from src.DBDefinitions import AdmissionApplicantModel

        user = getUserFromInfo(info=info) or {}
        user_id = user.get("id")
        firstname = user.get("name") or user.get("firstname")
        lastname = user.get("surname") or user.get("lastname")
        if not user_id:
            return InsertError[AdmissionApplicantGQLModel](
                msg="Missing authenticated user id",
                code="2a8c5f2a-0b5e-4b0e-8a88-6a4d2a9f33d1",
                location="admissionApplicantInit",
                _input=applicant
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
            return InsertError[AdmissionApplicantGQLModel](
                msg="Missing user name or surname in context",
                code="5d5a7c7a-1f8d-4c2c-8f70-2c2db6f5c9a2",
                location="admissionApplicantInit",
                _input=applicant
            )

        loader = AdmissionApplicantGQLModel.getLoader(info=info)
        stmt = select(AdmissionApplicantModel.id).where(
            AdmissionApplicantModel.applicant_user_id == user_id
        )
        result = await loader.session.execute(stmt)
        existing_id = result.scalars().first()
        if existing_id is not None:
            return InsertError[AdmissionApplicantGQLModel](
                msg="Applicant profile already exists for this user",
                code="e7f2f3c3-0e6d-4a9a-8c1a-5c7a621f8a1c",
                location="admissionApplicantInit",
                _input=applicant
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
        return await Insert[AdmissionApplicantGQLModel].DoItSafeWay(info=info, entity=applicant_data)

    @strawberry.mutation(description="Insert admission applicant", permission_classes=[OnlyForAuthentized])
    async def admission_applicant_insert(
        self,
        info: strawberry.Info,
        applicant: AdmissionApplicantInsertGQLModel
    ) -> typing.Union[AdmissionApplicantGQLModel, InsertError[AdmissionApplicantGQLModel]]:
        from uoishelpers.resolvers import Insert

        return await Insert[AdmissionApplicantGQLModel].DoItSafeWay(info=info, entity=applicant)

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
        from uoishelpers.resolvers import Update

        return await Update[AdmissionApplicantGQLModel].DoItSafeWay(info=info, entity=applicant)

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
        from uoishelpers.resolvers import Delete

        return await Delete[AdmissionApplicantGQLModel].DoItSafeWay(info=info, entity=applicant)
