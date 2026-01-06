from typing import Optional
from src.DBDefinitions import (
    BaseModel,
    EventModel,
    EventInvitationModel,
    AdmissionProcessModel,
    AdmissionApplicationModel,
    StudyProgramModel,
    PaymentInfoModel,
)
from src.DBDefinitions.EnrollmentModel import EnrollmentModel
from src.DBDefinitions.PaymentModel import PaymentModel

from uoishelpers.dataloaders.LoaderMapBase import LoaderMapBase
from uoishelpers.dataloaders.IDLoader import IDLoader



class LoaderMap(LoaderMapBase[BaseModel]):
    BaseModel = BaseModel

    EventModel: Optional[IDLoader]  # only type hint, no assignment here
    EventInvitationModel: Optional[IDLoader]
    #StateModel: Optional[IDLoader]
    StudyProgramModel: Optional[IDLoader]
    PaymentInfoModel: Optional[IDLoader]
    AdmissionProcessModel: Optional[IDLoader]
    AdmissionApplicationModel: Optional[IDLoader]
    EnrollmentModel: Optional[IDLoader]
    PaymentModel: Optional[IDLoader]






    def __init__(self, session):
        super().__init__(session)

        self.EventModel = self.get(EventModel)
        self.EventInvitationModel = self.get(EventInvitationModel)
        self.StudyProgramModel = self.get(StudyProgramModel)
        self.PaymentInfoModel = self.get(PaymentInfoModel)
        self.AdmissionProcessModel = self.get(AdmissionProcessModel)
        self.AdmissionApplicationModel = self.get(AdmissionApplicationModel)
        self.EnrollmentModel = self.get(EnrollmentModel)
        self.PaymentModel = self.get(PaymentModel)

        #self.StateModel = self.get(StateModel)



def createLoadersContext(session):
    return {"loaders": LoaderMap(session)}
