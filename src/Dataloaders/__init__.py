from typing import Optional

from src.DBDefinitions import (
    BaseModel,
    AdmissionProcessModel,
    AdmissionApplicationModel,
    AdmissionPaymentModel,
    AdmissionPaymentInfoModel,
    ExamModel,
)

from uoishelpers.dataloaders.LoaderMapBase import LoaderMapBase
from uoishelpers.dataloaders.IDLoader import IDLoader


class LoaderMap(LoaderMapBase[BaseModel]):
    BaseModel = BaseModel

    AdmissionProcessModel: Optional[IDLoader]
    AdmissionApplicationModel: Optional[IDLoader]
    AdmissionPaymentModel: Optional[IDLoader]
    AdmissionPaymentInfoModel: Optional[IDLoader]
    ExamModel: Optional[IDLoader]

    def __init__(self, session):
        super().__init__(session)

        self.AdmissionProcessModel = self.get(AdmissionProcessModel)
        self.AdmissionApplicationModel = self.get(AdmissionApplicationModel)
        self.AdmissionPaymentModel = self.get(AdmissionPaymentModel)
        self.AdmissionPaymentInfoModel = self.get(AdmissionPaymentInfoModel)
        self.ExamModel = self.get(ExamModel)


def createLoadersContext(session):
    return {"loaders": LoaderMap(session)}
