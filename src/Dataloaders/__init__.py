from typing import Optional
from src.DBDefinitions import BaseModel, EventModel, EventInvitationModel, AdmissionModel
from src.DBDefinitions.EnrollmentModel import EnrollmentModel
from src.DBDefinitions.PaymentModel import PaymentModel
from src.DBDefinitions.StudyProgramModel import StudyProgramModel
from uoishelpers.dataloaders.LoaderMapBase import LoaderMapBase
from uoishelpers.dataloaders.IDLoader import IDLoader


class LoaderMap(LoaderMapBase[BaseModel]):
    BaseModel = BaseModel

    EventModel: Optional[IDLoader]  # only type hint, no assignment here
    EventInvitationModel: Optional[IDLoader]
    AdmissionModel: Optional[IDLoader]
    EnrollmentModel: Optional[IDLoader]
    PaymentModel: Optional[IDLoader]
    StudyProgramModel: Optional[IDLoader]


    def __init__(self, session):
        super().__init__(session)

        self.EventModel = self.get(EventModel)
        self.EventInvitationModel = self.get(EventInvitationModel)
        self.AdmissionModel = self.get(AdmissionModel)
        self.EnrollmentModel = self.get(EnrollmentModel)
        self.PaymentModel = self.get(PaymentModel)
        self.StudyProgramModel = self.get(StudyProgramModel)


def createLoadersContext(session):
    return {"loaders": LoaderMap(session)}
