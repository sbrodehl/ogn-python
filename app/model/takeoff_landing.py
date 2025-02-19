from app import db


class TakeoffLanding(db.Model):
    __tablename__ = "takeoff_landings"

    id = db.Column(db.Integer, primary_key=True)

    timestamp = db.Column(db.DateTime)
    is_takeoff = db.Column(db.Boolean)
    track = db.Column(db.SmallInteger)

    # Relations
    sender_id = db.Column(db.Integer, db.ForeignKey("senders.id", ondelete="CASCADE"))
    sender = db.relationship("Sender", foreign_keys=[sender_id], backref="takeoff_landings")

    airport_id = db.Column(db.Integer, db.ForeignKey("airports.id", ondelete="SET NULL"))
    airport = db.relationship("Airport", foreign_keys=[airport_id], backref="takeoff_landings")

    country_id = db.Column(db.Integer, db.ForeignKey("countries.gid", ondelete="CASCADE"), index=True)
    country = db.relationship("Country", foreign_keys=[country_id], backref="takeoff_landings")

    __table_args__ = (db.Index('idx_takeoff_landings_uc', 'timestamp', 'sender_id', 'airport_id', unique=True), )
