import strawberry


from .EventGQLModel import EventMutation
from .EventInvitationGQLModel import EventInvitationMutation
from .AdmissionProcessGQLModel import AdmissionProcessMutation
from .AdmissionApplicationGQLModel import AdmissionApplicationMutation
from .EnrollmentGQLModel import EnrollmentMutation
from .PaymentGQLModel import PaymentMutation
from .PaymentInfoGQLModel import PaymentInfoMutation
from .StudyProgramGQLModel import StudyProgramMutation



@strawberry.type(description="""Type for mutation root""")
class Mutation(EventMutation, EventInvitationMutation, AdmissionProcessMutation, AdmissionApplicationMutation, EnrollmentMutation, PaymentMutation, PaymentInfoMutation, StudyProgramMutation):
    pass
