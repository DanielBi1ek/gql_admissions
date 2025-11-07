import strawberry

from .AdmissionGQLModel import AdmissionQuery
from .EnrollmentGQLModel import EnrollmentQuery
from .EventGQLModel import EventQuery
from .EventInvitationGQLModel import EventInvitationQuery
from .PaymentGQLModel import PaymentQuery
from .StudyProgramGQLModel import StudyProgramQuery


@strawberry.type(description="""Type for query root (admissions only)""")
class Query(AdmissionQuery, EnrollmentQuery, EventQuery, EventInvitationQuery, PaymentQuery, StudyProgramQuery):
    pass
