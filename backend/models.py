from datetime import datetime, timezone
from secrets import token_urlsafe
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db


def now():
    return datetime.now(timezone.utc)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(20), nullable=False, default="student")
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    verification_token = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return bool(self.password_hash and check_password_hash(self.password_hash, password))

    def issue_verification_token(self):
        self.verification_token = token_urlsafe(32)
        return self.verification_token

    def as_dict(self):
        return {"id": self.id, "email": self.email, "name": self.name,
                "role": self.role, "is_verified": self.is_verified, "is_active": self.is_active}


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    academic_year = db.Column(db.String(9), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    invite_code = db.Column(db.String(32), unique=True, nullable=False, default=lambda: token_urlsafe(10))
    tutor_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    tutor = db.relationship("User", foreign_keys=[tutor_id])
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def as_dict(self):
        return {"id": self.id, "name": self.name, "academic_year": self.academic_year,
                "level": self.level, "invite_code": self.invite_code, "tutor_id": self.tutor_id,
                "tutor": self.tutor.as_dict() if self.tutor else None, "is_active": self.is_active}


class Enrollment(db.Model):
    __table_args__ = (db.UniqueConstraint("student_id", "course_id"),)
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    joined_at = db.Column(db.DateTime(timezone=True), default=now)
    student = db.relationship("User")
    course = db.relationship("Course")


class Aspect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, default="")
    order = db.Column(db.Integer, default=0)
    low_max = db.Column(db.Float, default=1.99)
    medium_max = db.Column(db.Float, default=2.99)
    low_message = db.Column(db.Text, default="Estás empezando: cada pequeño paso cuenta.")
    medium_message = db.Column(db.Text, default="Vas avanzando. Mantén la constancia.")
    high_message = db.Column(db.Text, default="Has construido una base sólida. Sigue creciendo.")
    items = db.relationship("Item", backref="aspect", cascade="all, delete-orphan", order_by="Item.order")

    def as_dict(self, include_items=True):
        data = {"id": self.id, "level": self.level, "name": self.name,
                "description": self.description, "order": self.order,
                "low_max": self.low_max, "medium_max": self.medium_max,
                "messages": {"incipiente": self.low_message, "en_desarrollo": self.medium_message,
                             "generado": self.high_message}}
        if include_items:
            data["items"] = [i.as_dict() for i in self.items]
        return data


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aspect_id = db.Column(db.Integer, db.ForeignKey("aspect.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)
    reverse_scored = db.Column(db.Boolean, default=False)
    help_text = db.Column(db.Text, default="")

    def as_dict(self):
        return {"id": self.id, "aspect_id": self.aspect_id, "text": self.text,
                "order": self.order, "reverse_scored": self.reverse_scored, "help_text": self.help_text}


class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now)
    encouragement = db.Column(db.Text, default="")
    student = db.relationship("User")
    course = db.relationship("Course")
    answers = db.relationship("Answer", backref="attempt", cascade="all, delete-orphan")


class Answer(db.Model):
    __table_args__ = (db.UniqueConstraint("attempt_id", "item_id"),)
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("attempt.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    item = db.relationship("Item")

