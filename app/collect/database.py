from io import StringIO
import csv
import requests

from sqlalchemy.dialects.postgresql import insert
from flask import current_app

from flydenity import parser as flydenity_parser

from app import db
from app.model import AircraftType, Country, Sender, SenderInfo, SenderInfoOrigin, Receiver

DDB_URL = "https://ddb.glidernet.org/download/?j=1&t=1"
FLARMNET_URL = "https://www.flarmnet.org/static/files/wfn/data.fln"


def upsert(model, rows, update_cols):
    """Insert rows in model. On conflicting update columns if new value IS NOT NULL."""

    table = model.__table__

    stmt = insert(table).values(rows)

    on_conflict_stmt = stmt.on_conflict_do_update(
        index_elements=table.primary_key.columns, set_={k: db.case([(getattr(stmt.excluded, k) != db.null(), getattr(stmt.excluded, k))], else_=getattr(model, k)) for k in update_cols}
    )

    # print(compile_query(on_conflict_stmt))
    return on_conflict_stmt


def read_ddb(csv_file=None):
    """Get SenderInfos. You can provide a local file path for user defined SenderInfos. Otherwise the SenderInfos will be fetched from official DDB."""

    if csv_file is None:
        sender_info_origin = SenderInfoOrigin.OGN_DDB
        r = requests.get(DDB_URL)
        rows = "\n".join(i for i in r.text.splitlines() if i[0] != "#")
    else:
        sender_info_origin = SenderInfoOrigin.USER_DEFINED
        r = open(csv_file, "r")
        rows = "".join(i for i in r.readlines() if i[0] != "#")

    data = csv.reader(StringIO(rows), quotechar="'", quoting=csv.QUOTE_ALL)

    sender_info_dicts = []
    for row in data:
        sender_info_dicts.append({
            'address_type': row[0],
            'address': row[1],
            'aircraft': row[2],
            'registration': row[3],
            'competition': row[4],
            'tracked': row[5] == "Y",
            'identified': row[6] == "Y",
            'aircraft_type': AircraftType(int(row[7])),
            'address_origin': sender_info_origin
        })

    return sender_info_dicts


def read_flarmnet(fln_file=None):
    import flarmnet
    if fln_file is None:
        from io import StringIO
        sender_info_origin = SenderInfoOrigin.FLARMNET
        r = requests.get(FLARMNET_URL)
        buffer = StringIO(r.text)
        reader = flarmnet.Reader(buffer)
    else:
        sender_info_origin = SenderInfoOrigin.USER_DEFINED  # TODO: USER_DEFINED_FLARM ?
        with open(fln_file, "rb") as file:
            reader = flarmnet.Reader(file)

    sender_info_dicts = []
    for record in reader.read():
        sender_info_dicts.append({
            'address': record.id,
            'aircraft': record.plane_type,
            'registration': record.registration,
            'competition': record.competition_id if record.competition_id else None,
            'address_origin': sender_info_origin
        })

    return sender_info_dicts


def merge_sender_infos(sender_info_dicts):
    for sender_info_dict in sender_info_dicts:
        statement = insert(SenderInfo) \
            .values(**sender_info_dict) \
            .on_conflict_do_update(
                index_elements=['address', 'address_origin'],
                set_=sender_info_dict)

        db.session.execute(statement)

    db.session.commit()

    # update sender_infos FK countries
    countries = {country.iso2: country for country in db.session.query(Country)}

    parser = flydenity_parser.Parser()
    for sender_info in db.session.query(SenderInfo).filter(SenderInfo.country_id == db.null()):
        datasets = parser.parse(sender_info.registration, strict=True)
        if datasets is None:
            continue

        for dataset in datasets:
            if 'iso2' in dataset:
                sender_info.country = countries[dataset['iso2']]
    db.session.commit()

    # Update sender_infos FK -> senders
    upd = db.update(SenderInfo) \
        .where(SenderInfo.address == Sender.address) \
        .values(sender_id=Sender.id)
    result = db.session.execute(upd)
    db.session.commit()

    return len(sender_info_dicts)
