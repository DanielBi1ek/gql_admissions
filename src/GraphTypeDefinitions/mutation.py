import strawberry


from .EventGQLModel import EventMutation
from .EventInvitationGQLModel import EventInvitationMutation
from .AdmissionGQLModel import AdmissionMutation
from .EnrollmentGQLModel import EnrollmentMutation
from .PaymentGQLModel import PaymentMutation
from .PaymentInfoGQLModel import PaymentInfoMutation



@strawberry.type(description="""Type for mutation root""")
class Mutation(EventMutation, EventInvitationMutation, AdmissionMutation, EnrollmentMutation, PaymentMutation, PaymentInfoMutation):
    pass
