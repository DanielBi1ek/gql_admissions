import strawberry

from .AdmissionProcessGQLModel import AdmissionProcessQuery
from .AdmissionApplicationGQLModel import AdmissionApplicationQuery
from .AdmissionPaymentGQLModel import AdmissionPaymentQuery
from .AdmissionPaymentInfoGQLModel import AdmissionPaymentInfoQuery
from .ExamGQLModel import ExamQuery


@strawberry.type(description="""Type for query root""")
class Query(
    AdmissionProcessQuery,
    AdmissionApplicationQuery,
    AdmissionPaymentQuery,
    AdmissionPaymentInfoQuery,
    ExamQuery,
):
    pass
