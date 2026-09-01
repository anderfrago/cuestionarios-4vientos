import csv
import io
from collections import defaultdict
from flask import Blueprint, Response, abort, current_app, jsonify, request, redirect, url_for
from flask_jwt_extended import create_access_token, jwt_required
from flask_mail import Message
from sqlalchemy import func
from .auth import current_user, roles_required
from .extensions import db, mail, oauth
from .models import Answer, Aspect, Attempt, Course, Enrollment, Item, User

api = Blueprint("api", __name__, url_prefix="/api")


def payload():
    return request.get_json(silent=True) or {}


def error(message, status=400):
    return jsonify({"error": message}), status


def allowed_course(user, course):
    return user.role == "admin" or (user.role == "tutor" and course.tutor_id == user.id)


def attempt_dict(attempt, include_answers=False):
    grouped = defaultdict(list)
    for answer in attempt.answers:
        score = 5 - answer.value if answer.item.reverse_scored else answer.value
        grouped[answer.item.aspect].append(score)
    results = []
    for aspect, values in grouped.items():
        average = round(sum(values) / len(values), 2)
        if average <= aspect.low_max:
            level, message = "Incipiente", aspect.low_message
        elif average <= aspect.medium_max:
            level, message = "En desarrollo", aspect.medium_message
        else:
            level, message = "Generado", aspect.high_message
        results.append({"aspect_id": aspect.id, "aspect": aspect.name, "average": average,
                        "level": level, "message": message})
    data = {"id": attempt.id, "created_at": attempt.created_at.isoformat(),
            "student": attempt.student.as_dict(), "course": attempt.course.as_dict(),
            "encouragement": attempt.encouragement, "results": sorted(results, key=lambda r: r["aspect_id"])}
    if include_answers:
        data["answers"] = [{"item_id": a.item_id, "text": a.item.text, "value": a.value}
                           for a in attempt.answers]
    return data


@api.get("/health")
def health():
    return {"status": "ok"}


@api.post("/auth/register")
def register():
    data = payload()
    email = data.get("email", "").strip().lower()
    if not email or "@" not in email or len(data.get("password", "")) < 8 or not data.get("name"):
        return error("Nombre, correo válido y contraseña de al menos 8 caracteres son obligatorios")
    if User.query.filter_by(email=email).first():
        return error("Ya existe una cuenta con ese correo", 409)
    role = "admin" if email in current_app.config["ADMIN_EMAILS"] else "student"
    user = User(email=email, name=data["name"].strip(), role=role,
                is_verified=role == "admin" or not current_app.config.get("MAIL_USERNAME"))
    user.set_password(data["password"])
    token = user.issue_verification_token()
    db.session.add(user)
    db.session.commit()
    if current_app.config.get("MAIL_USERNAME"):
        link = f'{current_app.config["FRONTEND_URL"]}/verificar/{token}'
        mail.send(Message("Verifica tu cuenta", recipients=[email], body=f"Verifica tu cuenta: {link}"))
    return jsonify({"message": "Cuenta creada. Revisa tu correo para verificarla.",
                    "verification_required": not user.is_verified}), 201


@api.get("/auth/verify/<token>")
def verify(token):
    user = User.query.filter_by(verification_token=token).first_or_404()
    user.is_verified, user.verification_token = True, None
    db.session.commit()
    return {"message": "Correo verificado"}


@api.post("/auth/login")
def login():
    data = payload()
    user = User.query.filter(func.lower(User.email) == data.get("email", "").strip().lower()).first()
    if not user or not user.check_password(data.get("password", "")):
        return error("Credenciales incorrectas", 401)
    if not user.is_active or not user.is_verified:
        return error("La cuenta está inactiva o pendiente de verificación", 403)
    return {"access_token": create_access_token(identity=str(user.id)), "user": user.as_dict()}


@api.get("/auth/google")
def google_login():
    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        return error("Google OAuth no está configurado", 503)
    return oauth.google.authorize_redirect(url_for("api.google_callback", _external=True))


@api.get("/auth/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    info = token.get("userinfo") or oauth.google.userinfo()
    email = info["email"].lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        role = "admin" if email in current_app.config["ADMIN_EMAILS"] else "student"
        user = User(email=email, name=info.get("name", email.split("@")[0]), role=role,
                    is_verified=True)
        db.session.add(user)
    else:
        user.is_verified = True
    db.session.commit()
    access = create_access_token(identity=str(user.id))
    return redirect(f'{current_app.config["FRONTEND_URL"]}/acceso?token={access}')


@api.get("/me")
@jwt_required()
def me():
    user = current_user()
    courses = Course.query.join(Enrollment).filter(Enrollment.student_id == user.id).all() if user.role == "student" else Course.query.filter_by(tutor_id=user.id).all()
    return {"user": user.as_dict(), "courses": [c.as_dict() for c in courses]}


@api.post("/courses/join")
@roles_required("student")
def join_course():
    course = Course.query.filter_by(invite_code=payload().get("code"), is_active=True).first()
    if not course:
        return error("Código de curso no válido", 404)
    user = current_user()
    if not Enrollment.query.filter_by(student_id=user.id, course_id=course.id).first():
        db.session.add(Enrollment(student_id=user.id, course_id=course.id))
        db.session.commit()
    return course.as_dict(), 201


@api.get("/courses/<int:course_id>/questionnaire")
@jwt_required()
def questionnaire(course_id):
    user, course = current_user(), Course.query.get_or_404(course_id)
    enrolled = Enrollment.query.filter_by(student_id=user.id, course_id=course.id).first()
    if not (enrolled or allowed_course(user, course)):
        abort(403)
    aspects = Aspect.query.filter_by(level=course.level).order_by(Aspect.order).all()
    return {"course": course.as_dict(), "scale": [
        {"value": 1, "label": "Nunca"}, {"value": 2, "label": "A veces"},
        {"value": 3, "label": "En la mayoría de las veces"}, {"value": 4, "label": "Siempre"}],
        "aspects": [a.as_dict() for a in aspects]}


@api.post("/courses/<int:course_id>/attempts")
@roles_required("student")
def submit_attempt(course_id):
    user, data = current_user(), payload()
    course = Course.query.get_or_404(course_id)
    if not Enrollment.query.filter_by(student_id=user.id, course_id=course.id).first():
        abort(403)
    expected = {i.id: i for a in Aspect.query.filter_by(level=course.level) for i in a.items}
    answers = {int(a["item_id"]): int(a["value"]) for a in data.get("answers", [])}
    if set(answers) != set(expected) or any(v not in range(1, 5) for v in answers.values()):
        return error("Debes responder todos los ítems con valores entre 1 y 4")
    attempt = Attempt(student_id=user.id, course_id=course.id,
                      encouragement="Gracias por escucharte. Reconocer cómo estás es el primer paso para seguir creciendo.")
    db.session.add(attempt)
    db.session.flush()
    db.session.add_all([Answer(attempt_id=attempt.id, item_id=i, value=v) for i, v in answers.items()])
    db.session.commit()
    return attempt_dict(attempt), 201


@api.get("/attempts")
@jwt_required()
def attempts():
    user = current_user()
    rows = Attempt.query.filter_by(student_id=user.id).order_by(Attempt.created_at.desc()).all()
    return [attempt_dict(a) for a in rows]


@api.get("/courses/<int:course_id>/analytics")
@roles_required("tutor", "admin")
def analytics(course_id):
    course, user = Course.query.get_or_404(course_id), current_user()
    if not allowed_course(user, course):
        abort(403)
    attempts = Attempt.query.filter_by(course_id=course.id).order_by(Attempt.created_at).all()
    detail = [attempt_dict(a) for a in attempts]
    aspect_values = defaultdict(list)
    for attempt in detail:
        for result in attempt["results"]:
            aspect_values[result["aspect"]].append(result["average"])
    summary = [{"aspect": name, "average": round(sum(values) / len(values), 2), "count": len(values)}
               for name, values in aspect_values.items()]
    return {"course": course.as_dict(), "summary": summary, "attempts": detail}


@api.get("/courses/<int:course_id>/export.csv")
@roles_required("tutor", "admin")
def export_course(course_id):
    course, user = Course.query.get_or_404(course_id), current_user()
    if not allowed_course(user, course): abort(403)
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(["alumno", "correo", "fecha", "aspecto", "media", "nivel"])
    for attempt in Attempt.query.filter_by(course_id=course.id):
        for result in attempt_dict(attempt)["results"]:
            writer.writerow([attempt.student.name, attempt.student.email, attempt.created_at.isoformat(),
                             result["aspect"], result["average"], result["level"]])
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="curso-{course.id}.csv"'})


@api.route("/admin/courses", methods=["GET", "POST"])
@roles_required("admin")
def admin_courses():
    if request.method == "GET": return [c.as_dict() for c in Course.query.all()]
    data = payload(); course = Course(name=data["name"], academic_year=data["academic_year"],
                                     level=int(data["level"]), tutor_id=data.get("tutor_id"))
    db.session.add(course); db.session.commit(); return course.as_dict(), 201


@api.route("/admin/courses/<int:course_id>", methods=["PUT", "DELETE"])
@roles_required("admin")
def admin_course(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == "DELETE":
        course.is_active = False; db.session.commit(); return "", 204
    for key in ("name", "academic_year", "level", "tutor_id", "is_active"):
        if key in payload(): setattr(course, key, payload()[key])
    db.session.commit(); return course.as_dict()


@api.route("/admin/users", methods=["GET", "POST"])
@roles_required("admin")
def admin_users():
    if request.method == "GET": return [u.as_dict() for u in User.query.order_by(User.name).all()]
    data = payload(); user = User(email=data["email"].lower(), name=data["name"],
                                 role=data.get("role", "student"), is_verified=True)
    user.set_password(data.get("password", "Cambiar123!")); db.session.add(user); db.session.commit()
    return user.as_dict(), 201


@api.route("/admin/users/<int:user_id>", methods=["PUT", "DELETE"])
@roles_required("admin")
def admin_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "DELETE": user.is_active = False
    else:
        data = payload()
        for key in ("name", "role", "is_active", "is_verified"):
            if key in data: setattr(user, key, data[key])
    db.session.commit(); return ("", 204) if request.method == "DELETE" else user.as_dict()


@api.route("/admin/aspects", methods=["GET", "POST"])
@roles_required("admin")
def admin_aspects():
    if request.method == "GET": return [a.as_dict() for a in Aspect.query.order_by(Aspect.level, Aspect.order)]
    data = payload(); aspect = Aspect(**{k: data[k] for k in ("level", "name")}, order=data.get("order", 0))
    db.session.add(aspect); db.session.commit(); return aspect.as_dict(), 201


@api.route("/admin/aspects/<int:aspect_id>", methods=["PUT", "DELETE"])
@roles_required("admin")
def admin_aspect(aspect_id):
    aspect = Aspect.query.get_or_404(aspect_id)
    if request.method == "DELETE": db.session.delete(aspect); db.session.commit(); return "", 204
    data = payload()
    for key in ("name", "description", "order", "low_max", "medium_max", "low_message", "medium_message", "high_message"):
        if key in data: setattr(aspect, key, data[key])
    db.session.commit(); return aspect.as_dict()


@api.route("/admin/items", methods=["POST"])
@roles_required("admin")
def admin_item_create():
    data = payload(); item = Item(aspect_id=data["aspect_id"], text=data["text"], order=data.get("order", 0),
                                  reverse_scored=data.get("reverse_scored", False))
    db.session.add(item); db.session.commit(); return item.as_dict(), 201


@api.route("/admin/items/<int:item_id>", methods=["PUT", "DELETE"])
@roles_required("admin")
def admin_item(item_id):
    item = Item.query.get_or_404(item_id)
    if request.method == "DELETE": db.session.delete(item); db.session.commit(); return "", 204
    data = payload()
    for key in ("text", "order", "reverse_scored", "help_text", "aspect_id"):
        if key in data: setattr(item, key, data[key])
    db.session.commit(); return item.as_dict()
