import strawberry

from .AdmissionProcessGQLModel import AdmissionProcessQuery
from .AdmissionApplicationGQLModel import AdmissionApplicationQuery
from .AdmissionPaymentGQLModel import AdmissionPaymentQuery
from .AdmissionPaymentInfoGQLModel import AdmissionPaymentInfoQuery
from .ExamGQLModel import ExamQuery
from .UserPermissionQuery import UserPermissionQuery


@strawberry.type(description="""Type for query root""")
class Query(
    AdmissionProcessQuery,
    AdmissionApplicationQuery,
    AdmissionPaymentQuery,
    AdmissionPaymentInfoQuery,
    ExamQuery,
    UserPermissionQuery,
):
    pass
