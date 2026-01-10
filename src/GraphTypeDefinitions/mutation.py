import strawberry

from .AdmissionProcessGQLModel import AdmissionProcessMutation
from .AdmissionApplicationGQLModel import AdmissionApplicationMutation
from .AdmissionPaymentGQLModel import AdmissionPaymentMutation
from .AdmissionPaymentInfoGQLModel import AdmissionPaymentInfoMutation
from .AdmissionOfferGQLModel import AdmissionOfferMutation


@strawberry.type(description="""Type for mutation root""")
class Mutation(
    AdmissionProcessMutation,
    AdmissionApplicationMutation,
    AdmissionPaymentMutation,
    AdmissionPaymentInfoMutation,
    AdmissionOfferMutation,
):
    pass
