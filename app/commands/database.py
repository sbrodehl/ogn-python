from flask import current_app
from flask.cli import AppGroup
import click

from datetime import datetime
from sqlalchemy.sql import func

from app.model import SenderPosition
from app.utils import get_airports, get_days
from app.collect.timescaledb_views import create_timescaledb_views, create_views
from app.collect.database import read_ddb, read_flarmnet, merge_sender_infos

from app import db

user_cli = AppGroup("database")
user_cli.help = "Database creation and handling."


ALEMBIC_CONFIG_FILE = "alembic.ini"


def get_database_days(start, end):
    """Returns the first and the last day in aircraft_beacons table."""

    if start is None and end is None:
        days_from_db = db.session.query(func.min(SenderPosition.timestamp).label("first_day"), func.max(SenderPosition.timestamp).label("last_day")).one()
        start = days_from_db[0].date()
        end = days_from_db[1].date()
    else:
        start = datetime.strptime(start, "%Y-%m-%d").date()
        end = datetime.strptime(end, "%Y-%m-%d").date()

    days = get_days(start, end)

    return days


@user_cli.command("info")
def info():
    print(current_app.config)
    print(current_app.config["SQLALCHEMY_DATABASE_URI"])


@user_cli.command("init")
def init():
    """Initialize the database (with PostGIS and TimescaleDB extensions)."""

    from alembic.config import Config
    from alembic import command

    # Create PostGIS and PostGIS extensions
    db.session.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    # - enable raster support (for 3+)
    db.session.execute("CREATE EXTENSION IF NOT EXISTS postgis_raster;")
    db.session.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")
    db.session.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
    db.session.commit()

    # Create Scheme
    db.create_all()

    # Change (sender|receiver)_positions to TimescaleDB table
    db.session.execute("SELECT create_hypertable('sender_positions', 'reference_timestamp', chunk_time_interval => interval '3 hours', if_not_exists => TRUE);")
    db.session.execute("SELECT create_hypertable('receiver_positions', 'reference_timestamp', chunk_time_interval => interval '1 day', if_not_exists => TRUE);")
    db.session.commit()

    print("Initialized the database (with PostGIS and TimescaleDB extensions).")


@user_cli.command("drop")
@click.option("--sure", default="n")
def drop(sure):
    """Drop all tables."""
    if sure == "y":
        db.drop_all()
        print("Dropped all tables.")
    else:
        print("Add argument '--sure y' to drop all tables.")


@user_cli.command("import_ddb")
@click.option('--path', default=None, help='path to a local ddb file.')
def import_ddb(path):
    """Import registered devices from the DDB."""

    if path is None:
        print("Import registered devices fom the DDB...")
        sender_info_dicts = read_ddb()
    else:
        print("Import registered devices from '{}'...".format(path))
        sender_info_dicts = read_ddb(csv_file=path)
    counter = merge_sender_infos(sender_info_dicts)
    print("Imported %i devices." % counter)


@user_cli.command("import_flarmnet")
@click.argument("path")
def import_flarmnet(path=None):
    """Import registered devices from a local file."""

    print("Import registered devices from '{}'...".format("internet" if path is None else path))
    sender_info_dicts = read_flarmnet(fln_file=path)
    counter = merge_sender_infos(sender_info_dicts)
    print("Imported %i devices." % counter)


@user_cli.command("import_airports")
@click.argument("path")
def import_airports(path="tests/SeeYou.cup"):
    """Import airports from a ".cup" file"""

    print("Import airports from '{}'...".format(path))
    airports = get_airports(path)
    db.session.bulk_save_objects(airports)
    db.session.commit()
    # TODO: SRID 4087 ist nicht korrekt, aber spherical mercator 3857 wirft hier Fehler
    db.session.execute("UPDATE airports AS a SET border = ST_Transform(ST_Buffer(ST_Transform(location, 4087), 1.5 * GREATEST(500, a.runway_length)), 4326);")
    db.session.commit()
    print("Imported {} airports.".format(len(airports)))


@user_cli.command("create_timescaledb_views")
def cmd_create_timescaledb_views():
    """Create TimescaleDB views."""

    create_timescaledb_views()
    print("Done")


@user_cli.command("create_views")
def cmd_create_views():
    """Create views."""

    create_views()
    print("Done")
