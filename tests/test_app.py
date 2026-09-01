import pytest
from backend import create_app
from backend.extensions import db
from backend.models import Course, Enrollment, User


@pytest.fixture()
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                      "ADMIN_EMAILS": {"admin@example.com"}, "MAIL_USERNAME": None,
                      "JWT_SECRET_KEY": "test-key-that-is-longer-than-thirty-two-bytes",
                      "AUTO_CREATE_DB": True})
    yield app


@pytest.fixture()
def client(app): return app.test_client()


def register(client, email, name="Persona"):
    return client.post("/api/auth/register", json={"email": email, "name": name, "password": "Segura123!"})


def login(client, email):
    return client.post("/api/auth/login", json={"email": email, "password": "Segura123!"}).get_json()["access_token"]


def auth(token): return {"Authorization": f"Bearer {token}"}


def test_registration_login_and_admin_role(client):
    assert register(client, "admin@example.com").status_code == 201
    token = login(client, "admin@example.com")
    assert client.get("/api/me", headers=auth(token)).get_json()["user"]["role"] == "admin"


def test_admin_user_crud_and_safe_form_deletion(client):
    register(client, "admin@example.com")
    admin = login(client, "admin@example.com")
    created = client.post("/api/admin/users", headers=auth(admin), json={
        "name": "Tutor inicial", "email": "new-tutor@example.com",
        "password": "Segura123!", "role": "tutor",
    })
    assert created.status_code == 201
    user_id = created.get_json()["id"]
    updated = client.put(f"/api/admin/users/{user_id}", headers=auth(admin), json={
        "name": "Tutor editado", "email": "tutor@example.com", "role": "tutor",
    })
    assert updated.status_code == 200
    assert updated.get_json()["email"] == "tutor@example.com"
    assert client.delete(f"/api/admin/users/{user_id}", headers=auth(admin)).status_code == 204
    users = client.get("/api/admin/users", headers=auth(admin)).get_json()
    assert next(u for u in users if u["id"] == user_id)["is_active"] is False
    assert client.delete(f"/api/admin/users/{user_id}?permanent=true", headers=auth(admin)).status_code == 204
    users = client.get("/api/admin/users", headers=auth(admin)).get_json()
    assert all(u["id"] != user_id for u in users)

    course = client.post("/api/admin/courses", headers=auth(admin), json={
        "name": "Curso borrable", "academic_year": "2026-2027", "level": 1,
    }).get_json()
    assert client.delete(f'/api/admin/courses/{course["id"]}', headers=auth(admin)).status_code == 204
    courses = client.get("/api/admin/courses", headers=auth(admin)).get_json()
    assert next(c for c in courses if c["id"] == course["id"])["is_active"] is False
    restored_course = client.put(f'/api/admin/courses/{course["id"]}', headers=auth(admin),
                                 json={"is_active": True})
    assert restored_course.status_code == 200
    assert restored_course.get_json()["is_active"] is True
    assert client.delete(f'/api/admin/courses/{course["id"]}', headers=auth(admin)).status_code == 204
    assert client.delete(f'/api/admin/courses/{course["id"]}?permanent=true',
                         headers=auth(admin)).status_code == 204
    courses = client.get("/api/admin/courses", headers=auth(admin)).get_json()
    assert all(c["id"] != course["id"] for c in courses)

    form = client.get("/api/admin/questionnaires", headers=auth(admin)).get_json()[0]
    assert client.delete(f'/api/admin/questionnaires/{form["id"]}', headers=auth(admin)).status_code == 204
    restored = client.put(f'/api/admin/questionnaires/{form["id"]}', headers=auth(admin),
                          json={"is_archived": False})
    assert restored.status_code == 200
    assert restored.get_json()["is_archived"] is False


def test_student_joins_by_code_and_submits_complete_questionnaire(client, app):
    register(client, "admin@example.com"); register(client, "student@example.com")
    admin_token, student_token = login(client, "admin@example.com"), login(client, "student@example.com")
    course = client.post("/api/admin/courses", headers=auth(admin_token), json={"name":"DAW1","academic_year":"2026-2027","level":1}).get_json()
    assert client.post("/api/courses/join", headers=auth(student_token), json={"code":course["invite_code"]}).status_code == 201
    form = client.get(f'/api/courses/{course["id"]}/questionnaire', headers=auth(student_token)).get_json()
    answers = [{"item_id":i["id"],"value":3} for a in form["aspects"] for i in a["items"]]
    response = client.post(f'/api/courses/{course["id"]}/attempts', headers=auth(student_token), json={"answers":answers})
    assert response.status_code == 201
    assert response.get_json()["results"]


def test_tutor_cannot_see_another_course(client, app):
    register(client, "admin@example.com")
    with app.app_context():
        tutor = User(email="tutor@example.com", name="Tutor", role="tutor", is_verified=True); tutor.set_password("Segura123!")
        db.session.add(tutor); db.session.flush(); own=Course(name="A",academic_year="2026-2027",level=1,tutor_id=tutor.id); other=Course(name="B",academic_year="2026-2027",level=1)
        db.session.add_all([own,other]); db.session.commit(); other_id=other.id
    token=login(client,"tutor@example.com")
    assert client.get(f"/api/courses/{other_id}/analytics",headers=auth(token)).status_code==403


def test_versioned_form_alert_and_exports(client, tmp_path):
    register(client, "admin@example.com"); register(client, "student@example.com")
    admin, student = login(client, "admin@example.com"), login(client, "student@example.com")
    course = client.post("/api/admin/courses", headers=auth(admin),
        json={"name":"DAW1","academic_year":"2026-2027","level":1}).get_json()
    forms = client.get("/api/admin/questionnaires", headers=auth(admin)).get_json()
    form = next(f for f in forms if f["level"] == 1)
    assert client.put(f'/api/admin/courses/{course["id"]}/questionnaires', headers=auth(admin),
        json={"questionnaire_ids":[form["id"]]}).status_code == 200
    client.post("/api/courses/join", headers=auth(student), json={"code":course["invite_code"]})
    available = client.get(f'/api/courses/{course["id"]}/forms', headers=auth(student)).get_json()["forms"]
    version_id = available[0]["version_id"]
    definition = client.get(f'/api/courses/{course["id"]}/forms/{version_id}', headers=auth(student)).get_json()
    responses = []
    for aspect in definition["version"]["aspects"]:
        for question in aspect["questions"]:
            targets = question["rows"] or [None]
            for row in targets:
                response = {"question_id": question["id"], "row_id": row["id"] if row else None}
                if question["question_type"] == "text": response["text_value"] = "Respuesta abierta"
                else:
                    option = question["options"][1 if question["is_critical"] else 0]
                    response["option_id"] = option["id"]
                responses.append(response)
    submitted = client.post(f'/api/courses/{course["id"]}/forms/{version_id}/attempts',
        headers=auth(student), json={"responses":responses})
    assert submitted.status_code == 201
    analytics = client.get(f'/api/courses/{course["id"]}/form-analytics', headers=auth(admin)).get_json()
    assert len(analytics["attempts"]) == 1
    assert len(analytics["alerts"]) == 1
    assert client.put(f'/api/alerts/{analytics["alerts"][0]["id"]}/review', headers=auth(admin),
        json={"notes":"Protocolo activado"}).status_code == 200
    xlsx = client.get(f'/api/courses/{course["id"]}/export.xlsx', headers=auth(admin))
    pdf = client.get(f'/api/courses/{course["id"]}/export.pdf', headers=auth(admin))
    assert xlsx.status_code == 200 and xlsx.data[:2] == b"PK"
    assert pdf.status_code == 200 and pdf.data[:4] == b"%PDF"
    (tmp_path / "export.xlsx").write_bytes(xlsx.data)
    (tmp_path / "export.pdf").write_bytes(pdf.data)
    draft = client.post(f'/api/admin/questionnaires/{form["id"]}/versions', headers=auth(admin),
        json={"source_version_id":version_id}).get_json()
    assert draft["version"] == 2 and draft["status"] == "draft"
