import os

from uoishelpers.feeders import ImportModels
from uoishelpers.dataloaders import readJsonFile

from src.DBDefinitions import (
    EventModel,
    EventInvitationModel,
    AdmissionModel,
    EnrollmentModel,
    PaymentModel,
)

get_demodata = lambda: readJsonFile(jsonFileName="./systemdata.json")


async def initDB(asyncSessionMaker, filename="./systemdata.json"):
    dbModels = []

    isDemo = os.environ.get("DEMODATA", None) in ["True", "true", True]
    if isDemo:
        print("Demo mode", flush=True)
        dbModels = [
            EventModel,
            EventInvitationModel,
            AdmissionModel,
            EnrollmentModel,
            PaymentModel,
        ]

    jsonData = readJsonFile(filename)

    # merge optional additions file (keeps original systemdata.json intact)
    additionsPath = os.path.join(os.path.dirname(filename), "systemdata.additions.json")
    if os.path.exists(additionsPath):
        try:
            additions = readJsonFile(additionsPath)
            # additions is expected to be a dict with table arrays
            if isinstance(additions, dict) and isinstance(jsonData, dict):
                for key, value in additions.items():
                    if not isinstance(value, list):
                        # not a table array, just copy
                        jsonData[key] = value
                        continue

                    if key not in jsonData or not isinstance(jsonData[key], list):
                        # no existing rows, add the whole array (but dedupe within additions)
                        seen = set()
                        new_rows = []
                        for r in value:
                            if not isinstance(r, dict):
                                new_rows.append(r)
                                continue
                            rid = r.get("id")
                            if rid is None:
                                # keep rows without id
                                new_rows.append(r)
                                continue
                            if rid in seen:
                                continue
                            seen.add(rid)
                            new_rows.append(r)
                        jsonData[key] = new_rows
                        continue

                    # both exist and both are lists -> merge but skip duplicates by id
                    existing_rows = jsonData[key]
                    existing_ids = set()
                    for er in existing_rows:
                        if isinstance(er, dict) and er.get("id") is not None:
                            existing_ids.add(er.get("id"))

                    # also dedupe within the additions values
                    added_ids = set()
                    for r in value:
                        if not isinstance(r, dict):
                            existing_rows.append(r)
                            continue
                        rid = r.get("id")
                        if rid is None:
                            existing_rows.append(r)
                            continue
                        if rid in existing_ids or rid in added_ids:
                            # skip duplicates
                            continue
                        added_ids.add(rid)
                        existing_rows.append(r)
        except Exception as e:
            print(f"Failed to load additions file {additionsPath}: {e}")

    # --- normalize date-like fields in the JSON so SQLAlchemy inserts correct types ---
    import datetime as _dt

    def _parse_iso(v):
        if isinstance(v, str):
            try:
                # fromisoformat supports 'YYYY-MM-DDTHH:MM:SS' and optional offset
                return _dt.datetime.fromisoformat(v)
            except Exception:
                return v
        return v

    # For admissions, convert applied_date, created and lastchange if present
    if isinstance(jsonData, dict) and "admissions_evolution" in jsonData:
        for row in jsonData.get("admissions_evolution", []):
            if not isinstance(row, dict):
                continue
            if "applied_date" in row:
                row["applied_date"] = _parse_iso(row.get("applied_date"))
            if "created" in row:
                row["created"] = _parse_iso(row.get("created"))
            if "lastchange" in row:
                row["lastchange"] = _parse_iso(row.get("lastchange"))

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
        AdmissionModel,
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
                        if value is None: continue
                        if value not in ids: continue
                        if value not in done:
                            skip_this_id = True
                            break
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
