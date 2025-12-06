import os

from uoishelpers.feeders import ImportModels
from uoishelpers.dataloaders import readJsonFile

from src.DBDefinitions import (
    EventModel,
    EventInvitationModel,
    AdmissionModel,
    EnrollmentModel,
    PaymentModel,
    # ensure we can create placeholder users
    # UserModel is defined in BaseModel for metadata; import it for runtime insertion
)
from src.DBDefinitions.BaseModel import IDType
from src.DBDefinitions.BaseModel import UserModel, StateModel

get_demodata = lambda: readJsonFile(jsonFileName="./systemdata.json")


async def initDB(asyncSessionMaker, filename="./systemdata.json"):
    dbModels = []

    isDemo = os.environ.get("DEMODATA", None) in ["True", "true", True]
    if isDemo:
        print("Demo mode", flush=True)
        # Ensure users and states are created first (they are referenced by other models in seed)
        dbModels = [
            UserModel,
            StateModel,
            EventModel,
            EventInvitationModel,
            AdmissionModel,
            EnrollmentModel,
            PaymentModel,
        ]

    jsonData = readJsonFile(filename)

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

    # Detect referenced user IDs across JSON and create placeholder users for them
    referenced_user_keys = {"createdby_id", "changedby_id", "updatedby_id", "user_id", "createdby", "updatedby"}
    referenced_user_ids = set()
    if isinstance(jsonData, dict):
        for tablename, rows in jsonData.items():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                for key in referenced_user_keys:
                    v = row.get(key)
                    if v is None:
                        continue
                    try:
                        import uuid as _uuid
                        uid = _uuid.UUID(str(v))
                        referenced_user_ids.add(uid)
                    except Exception:
                        continue

    if referenced_user_ids:
        print(f"DBFeeder: detected {len(referenced_user_ids)} referenced user ids")
        # If jsonData doesn't already contain users, inject minimal user rows
        if isinstance(jsonData, dict) and "users" not in jsonData:
            jsonData["users"] = []
            for uid in referenced_user_ids:
                jsonData["users"].append({
                    "id": str(uid),
                    "display_name": f"seed user {str(uid)}"
                })

    # --- build ordered dbModels list so that UserModel and StateModel are inserted first ---
    model_map = {
        "users": UserModel,
        "states": StateModel,
        "events_evolution": EventModel,
        "event_invitations_evolution": EventInvitationModel,
        "admissions_evolution": AdmissionModel,
        "enrollments_evolution": EnrollmentModel,
        "payments_evolution": PaymentModel,
    }

    ordered_models = []
    # always ensure users and states are first
    for key in ["users", "states"]:
        if key in model_map:
            ordered_models.append(model_map[key])
    # then add any models present in jsonData in a stable order
    for key in ["events_evolution", "event_invitations_evolution", "admissions_evolution", "enrollments_evolution", "payments_evolution"]:
        if key in jsonData and key in model_map:
            ordered_models.append(model_map[key])

    # If DEMODATA was explicitly requested earlier, that list may be used; otherwise use ordered_models
    if isDemo:
        dbModels = dbModels  # keep explicit demo list (already set above)
    else:
        dbModels = ordered_models

    if referenced_user_ids:
        # Insert placeholder users before importing other models to satisfy FK constraints
        async with asyncSessionMaker() as session:
            users_to_create = []
            for uid in referenced_user_ids:
                # We will try to avoid duplicates by checking existing ids
                # Note: This simple check is done per-session and may be fine for initialization
                existing = await session.get(UserModel, uid)
                if existing is None:
                    users_to_create.append(UserModel(id=uid, display_name=f"seed user {str(uid)}"))
            if users_to_create:
                session.add_all(users_to_create)
                await session.commit()
                print(f"DBFeeder: inserted {len(users_to_create)} placeholder users into DB")

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
