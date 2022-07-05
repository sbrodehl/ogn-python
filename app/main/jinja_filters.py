import math

from app.main import bp
from app.model import Airport, Country, Sender, Receiver

from flask import url_for


@bp.app_template_filter()
def to_html_flag(obj):
    if obj is None:
        return ""

    if isinstance(obj, str):
        return f"""<img src="{url_for('static', filename='img/Transparent.gif')}" class="flag flag-{obj.lower()}" alt="{obj}"/> """

    elif isinstance(obj, Airport):
        return f"""<img src="{url_for('static', filename='img/Transparent.gif')}" class="flag flag-{obj.country_code.lower()}" alt="{obj.country_code}"/> """

    elif isinstance(obj, Country):
        return f"""<img src="{url_for('static', filename='img/Transparent.gif')}" class="flag flag-{obj.iso2.lower()}" alt="{obj.iso2}"/> """

    elif isinstance(obj, Sender):
        if obj is not None and len(obj.infos) > 0 and obj.infos[0].country is not None:
            return f"""<img src="{url_for('static', filename='img/Transparent.gif')}" class="flag flag-{obj.infos[0].country.iso2.lower()}" alt="{obj.infos[0].country.iso2}"/> """
        else:
            return ""

    elif isinstance(obj, Receiver):
        if obj.country:
            return f"""<img src="{url_for('static', filename='img/Transparent.gif')}" class="flag flag-{obj.country.iso2.lower()}" alt="{obj.country.iso2}"/> """
        else:
            return ""
    else:
        raise NotImplementedError(f"cant apply filter 'to_html_flag' to object {type(obj)}")


@bp.app_template_filter()
def to_html_link(obj):
    if isinstance(obj, Airport):
        airport = obj
        return f"""<a href="{url_for('main.airport_detail', airport_id=airport.id)}">{airport.name}</a>"""

    elif isinstance(obj, Sender):
        sender = obj
        if len(sender.infos) > 0 and len(sender.infos[0].registration) > 0:
            return f"""<a href="{url_for('main.sender_detail', sender_id=sender.id)}">{sender.infos[0].registration}</a>"""
        elif sender.address:
            return f"""<a href="{url_for('main.sender_detail', sender_id=sender.id)}">[{sender.address}]</a>"""
        else:
            return f"""<a href="{url_for('main.sender_detail', sender_id=sender.id)}">[{sender.name}]</a>"""

    elif isinstance(obj, Receiver):
        receiver = obj
        return f"""<a href="{url_for('main.receiver_detail', receiver_id=receiver.id)}">{receiver.name}</a>"""

    elif obj is None:
        return "-"

    else:
        raise NotImplementedError(f"cant apply filter 'to_html_link' to object {type(obj)}")


@bp.app_template_filter()
def to_ordinal(rad):
    deg = math.degrees(rad)
    if deg >= 337.5 or deg < 22.5:
        return "N"
    elif 22.5 <= deg < 67.5:
        return "NW"
    elif 67.5 <= deg < 112.5:
        return "W"
    elif 112.5 <= deg < 157.5:
        return "SW"
    elif 157.5 <= deg < 202.5:
        return "S"
    elif 202.5 <= deg < 247.5:
        return "SE"
    elif 247.5 <= deg < 292.5:
        return "E"
    elif 292.5 <= deg < 337.5:
        return "NE"
