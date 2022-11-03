from flask import Blueprint

bp = Blueprint("main", __name__)

import app.main.routes  # noqa
import app.main.jinja_filters  # noqa

__all__ = [
    "routes", "jinja_filters", "bp"
]
