import strawberry

from .AdmissionProcessGQLModel import AdmissionProcessQuery
from .AdmissionApplicationGQLModel import AdmissionApplicationQuery
from .EnrollmentGQLModel import EnrollmentQuery
from .EventGQLModel import EventQuery
from .EventInvitationGQLModel import EventInvitationQuery
from .PaymentGQLModel import PaymentQuery
from .PaymentInfoGQLModel import PaymentInfoQuery
from .StudyProgramGQLModel import StudyProgramQuery



@strawberry.type(description="""Type for query root (admissions only)""")
class Query(AdmissionProcessQuery, AdmissionApplicationQuery, EnrollmentQuery, EventQuery, EventInvitationQuery, PaymentQuery, PaymentInfoQuery, StudyProgramQuery):
    pass
