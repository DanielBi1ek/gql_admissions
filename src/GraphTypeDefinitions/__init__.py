import datetime
import strawberry

from .query import Query
from .mutation import Mutation

timedelta = strawberry.scalar(
    # NewType("TimeDelta", float),
    datetime.timedelta,
    name="timedelta",
    serialize=lambda v: v.total_seconds() / 60,
    parse_value=lambda v: datetime.timedelta(minutes=v),
)

from .BaseGQLModel import Relation
from .BaseGQLModel import BaseGQLModel
from .UserGQLModel import UserGQLModel
from .StudyProgramGQLModel import StudyProgramGQLModel
from .AdmissionBankAccountGQLModel import AdmissionBankAccountGQLModel
from .AdmissionApplicantGQLModel import AdmissionApplicantGQLModel
from .AdmissionOfferGQLModel import AdmissionOfferGQLModel
from .AdmissionPaymentInfoGQLModel import AdmissionPaymentInfoGQLModel
from .AdmissionPaymentGQLModel import AdmissionPaymentGQLModel
from .AdmissionProcessGQLModel import AdmissionProcessGQLModel
from .AdmissionApplicationGQLModel import AdmissionApplicationGQLModel
from uoishelpers.resolvers import InsertError, UpdateError, DeleteError

gql_types = (
    UserGQLModel,
    BaseGQLModel,
    StudyProgramGQLModel,
    AdmissionBankAccountGQLModel,
    AdmissionApplicantGQLModel,
    AdmissionOfferGQLModel,
    AdmissionPaymentInfoGQLModel,
    AdmissionPaymentGQLModel,
    AdmissionProcessGQLModel,
    AdmissionApplicationGQLModel,
)

error_types = (
    InsertError[AdmissionBankAccountGQLModel],
    UpdateError[AdmissionBankAccountGQLModel],
    DeleteError[AdmissionBankAccountGQLModel],
    InsertError[AdmissionApplicantGQLModel],
    UpdateError[AdmissionApplicantGQLModel],
    DeleteError[AdmissionApplicantGQLModel],
    InsertError[AdmissionOfferGQLModel],
    UpdateError[AdmissionOfferGQLModel],
    DeleteError[AdmissionOfferGQLModel],
    InsertError[AdmissionPaymentInfoGQLModel],
    UpdateError[AdmissionPaymentInfoGQLModel],
    DeleteError[AdmissionPaymentInfoGQLModel],
    InsertError[AdmissionPaymentGQLModel],
    UpdateError[AdmissionPaymentGQLModel],
    DeleteError[AdmissionPaymentGQLModel],
    InsertError[AdmissionProcessGQLModel],
    UpdateError[AdmissionProcessGQLModel],
    DeleteError[AdmissionProcessGQLModel],
    InsertError[AdmissionApplicationGQLModel],
    UpdateError[AdmissionApplicationGQLModel],
    DeleteError[AdmissionApplicationGQLModel],
)

schema = strawberry.federation.Schema(
    query=Query,
    mutation=Mutation,
    types=(
        *gql_types,
        *error_types,
    ),
    scalar_overrides={datetime.timedelta: timedelta._scalar_definition},

    extensions=[],
    schema_directives=[Relation]

)

from uoishelpers.schema import WhoAmIExtension, ProfilingExtension, PrometheusExtension
import uoishelpers.schema.WhoAmIExtension as whoami_module

whoami_module.mequery = """
{
  me {
    id
    name
    surname
    fullname
    email
    roles(where: {valid: {_eq: true}}, limit: 1000) {
      valid
      group { id name }
      roletype { id name }
    }
  }
}"""
WhoAmIExtension.mequery = whoami_module.mequery

class LocalWhoAmIExtension(WhoAmIExtension):
    async def on_execute(self):
        ctx = self.execution_context.context
        existing_user = ctx.get("user")
        if ctx.get("_skip_whoami"):
            if existing_user is None:
                if ctx.get("_allow_anonymous"):
                    ctx["user"] = None
                else:
                    ctx["user"] = {}
            ctx.setdefault("ug_client", self.ug_query)
            yield
            return

        query = self.execution_context.query
        skip_queries = {
            getattr(whoami_module, "apolloQuery", None),
            getattr(whoami_module, "graphiQLQuery", None),
            getattr(whoami_module, "sdlQuery", None),
        }

        whoami = existing_user or {}
        if query not in skip_queries:
            try:
                response = await self.ug_query(query=whoami_module.mequery)
                whoami = response["data"].get("me")
            except Exception:
                whoami = existing_user or {}

        ctx["user"] = whoami or {}
        ctx["ug_client"] = self.ug_query
        yield

schema.extensions.append(LocalWhoAmIExtension)
schema.extensions.append(ProfilingExtension)
schema.extensions.append(PrometheusExtension(prefix="GQL_Evolution"))

from uoishelpers.gqlpermissions.RolePermissionSchemaExtension import RolePermissionSchemaExtension

schema.extensions.append(RolePermissionSchemaExtension)
