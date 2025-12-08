import typing
import strawberry
from .BaseGQLModel import IDType


@strawberry.federation.type(keys=["id"], extend=True)
class UserGQLModel:
    """
    External User type from gql_ug service.
    This extends the User type defined in the UG service.
    """
    id: IDType = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: IDType):
        # Federation will resolve the full user from gql_ug service
        return cls(id=id)