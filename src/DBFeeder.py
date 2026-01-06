import os

from functools import cache
from uoishelpers.feeders import ImportModels
from uoishelpers.dataloaders import readJsonFile

from src.DBDefinitions import (
    EventModel,
    EventInvitationModel,
    StudyProgramModel,
    AdmissionProcessModel,
    AdmissionApplicationModel,
    EnrollmentModel,
    PaymentInfoModel,
    PaymentModel,


)

get_demodata = lambda: readJsonFile(jsonFileName="./systemdata.json")


async def initDB(asyncSessionMaker, filename="./systemdata.json"):
    dbModels = [
    ]

    isDemo = os.environ.get("DEMODATA", None) in ["True", "true", True]
    if isDemo:
        print("Demo mode", flush=True)
        dbModels = [
            EventModel,
            EventInvitationModel,
            StudyProgramModel,
            PaymentInfoModel,
            AdmissionProcessModel,
            AdmissionApplicationModel,
            EnrollmentModel,
            PaymentModel,


        ]

    jsonData = readJsonFile(filename)
    import datetime as _dt

    def _parse_iso(v):
        if isinstance(v, str):
            try:
                return _dt.datetime.fromisoformat(v)
            except Exception:
                return v
        return v

    if isinstance(jsonData, dict) and "admission_processes" in jsonData:
        for row in jsonData.get("admission_processes", []):
            if not isinstance(row, dict):
                continue
            for key in [
                "application_start_date",
                "application_end_date",
                "exam_start_date",
                "exam_end_date",
                "decision_deadline",
                "payment_deadline",
                "enrollment_date",
                "condition_deadline",
                "condition_extended_deadline",
                "created",
                "lastchange",
            ]:
                if key in row:
                    row[key] = _parse_iso(row.get(key))

    if isinstance(jsonData, dict) and "admission_applications" in jsonData:
        for row in jsonData.get("admission_applications", []):
            if not isinstance(row, dict):
                continue
            for key in ["applied_date", "created", "lastchange"]:
                if key in row:
                    row[key] = _parse_iso(row.get(key))

    if isinstance(jsonData, dict) and "payments" in jsonData:
        for row in jsonData.get("payments", []):
            if not isinstance(row, dict):
                continue
            for key in ["paid_at", "created", "lastchange"]:
                if key in row:
                    row[key] = _parse_iso(row.get(key))

    if isinstance(jsonData, dict) and "enrollments" in jsonData:
        for row in jsonData.get("enrollments", []):
            if not isinstance(row, dict):
                continue
            for key in ["enrolled_at", "created", "lastchange"]:
                if key in row:
                    row[key] = _parse_iso(row.get(key))
    await ImportModels(asyncSessionMaker, dbModels, jsonData)

    print("Data initialized", flush=True)


async def backupDB(asyncSessionMaker, filename="./systemdata.backup.json"):
    import sqlalchemy
    import dataclasses
    import json
    from src.DBDefinitions.BaseModel import IDType

    dbModels = [
        EventModel,
        EventInvitationModel,
        StudyProgramModel,
        PaymentInfoModel,
        AdmissionProcessModel,
        AdmissionApplicationModel,
        EnrollmentModel,
        PaymentModel,


    ]
    data = []
    async with asyncSessionMaker() as session:
        for model in dbModels:
            sqlquery = sqlalchemy.select(model)
            rows = await session.execute(sqlquery)
            # vsechny radky do dict
            rowsdict = {}
            for row in rows:
                # print(row)
                asdict = dataclasses.asdict(row[0])
                id = asdict.get("id", None)
                if id is None: continue
                rowsdict[id] = asdict
            # vsechny primarní klice do ids
            ids = set(rowsdict.keys())
            todo = set()
            done = set()
            chunk_id = 0
            while len(done) < len(ids):
                for row in rowsdict.values():
                    id = row.get("id", None)
                    if id in done: continue
                    skip_this_id = False
                    for key, value in row.items():
                        if key == "id": continue
                        # if not isinstance(value, IDType): continue
                        if value is None: continue
                        if value not in ids: continue
                        if value not in done:
                            # print(row, key, value)
                            skip_this_id = True
                            break
                            # primarni klic je zpracovatelny, nemame zavislost na nezpracovanych klicich
                    if skip_this_id: continue
                    row["_chunk"] = chunk_id
                    todo.add(id)
                print(f"{model.__tablename__} chunk {chunk_id} todo/done/all {len(todo)}/{len(done)}/{len(ids)}")
                if len(todo) == 0: break
                done = done.union(todo)
                todo = set()
                chunk_id += 1
            data.append({
                model.__tablename__: list(rowsdict.values())
            })
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False, default=str)

    print("backup done", flush=True)
