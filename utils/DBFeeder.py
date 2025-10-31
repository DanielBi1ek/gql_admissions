import logging
from functools import cache
from DBDefinitions import (
    EventModel, EventUserModel, AdmissionModel, PaymentModel, EnrollmentModel
    )
from sqlalchemy.future import select



import os
import json
from uoishelpers.feeders import ImportModels
import datetime
import uuid

def get_demodata():
    def datetime_parser(json_dict):
        for (key, value) in json_dict.items():
            # match all date-like keys
            if any(sub in key for sub in ["date", "created", "lastchange"]):
                dateValueWOtzinfo = None
                if value is not None:
                    try:
                        # handle both "YYYY-MM-DDTHH:MM:SS" and "YYYY-MM-DD HH:MM:SS"
                        dateValue = datetime.datetime.fromisoformat(value.replace("T", " "))
                        dateValueWOtzinfo = dateValue.replace(tzinfo=None)
                    except Exception as e:
                        logging.error(f'jsonconvert Error "{key}": "{value}" ({e})')
                        dateValueWOtzinfo = None
                json_dict[key] = dateValueWOtzinfo

            # convert any UUID-like key
            elif "id" in key and value is not None:
                json_dict[key] = uuid.UUID(value)

        return json_dict

    with open("./systemdata.json", "r", encoding='utf-8') as f:
        jsonData = json.load(f, object_hook=datetime_parser)

    return jsonData

async def initDB(asyncSessionMaker):

    defaultNoDemo = "False"
    default = "True"
    dbModels = []
    if not(default == os.environ.get("DEMO", defaultNoDemo)):
        dbModels = dbModels + [
            EventModel,
            EventUserModel,
            AdmissionModel,
            PaymentModel,
            EnrollmentModel


        ]

    jsonData = get_demodata()
    await ImportModels(asyncSessionMaker, dbModels, jsonData)
    pass