import strawberry

from .AdmissionProcessGQLModel import AdmissionProcessMutation
from .AdmissionApplicationGQLModel import AdmissionApplicationMutation
from .AdmissionPaymentGQLModel import AdmissionPaymentMutation
from .AdmissionPaymentInfoGQLModel import AdmissionPaymentInfoMutation
from .AdmissionOfferGQLModel import AdmissionOfferMutation
from .AdmissionBankAccountGQLModel import AdmissionBankAccountMutation


@strawberry.type(description="""Type for mutation root""")
class Mutation(
    AdmissionProcessMutation,
    AdmissionApplicationMutation,
    AdmissionPaymentMutation,
    AdmissionPaymentInfoMutation,
    AdmissionOfferMutation,
    AdmissionBankAccountMutation,
):
    pass
