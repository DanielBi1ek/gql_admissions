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

schema = strawberry.federation.Schema(
    query=Query,
    mutation=Mutation,
    types=(UserGQLModel, BaseGQLModel, StudyProgramGQLModel, AdmissionBankAccountGQLModel, AdmissionApplicantGQLModel),
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

schema.extensions.append(WhoAmIExtension)
schema.extensions.append(ProfilingExtension)
schema.extensions.append(PrometheusExtension(prefix="GQL_Evolution"))

from uoishelpers.gqlpermissions.RolePermissionSchemaExtension import RolePermissionSchemaExtension

schema.extensions.append(RolePermissionSchemaExtension)
