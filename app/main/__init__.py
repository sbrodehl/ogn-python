from flask import Blueprint

bp = Blueprint("main", __name__)

import app.main.routes
import app.main.jinja_filters

__all__ = [
    "routes", "jinja_filters", "bp"
]
