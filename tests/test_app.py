import pytest
from backend import create_app
from backend.extensions import db
from backend.models import Course, Enrollment, User


@pytest.fixture()
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                      "ADMIN_EMAILS": {"admin@example.com"}, "MAIL_USERNAME": None,
                      "JWT_SECRET_KEY": "test-key-that-is-longer-than-thirty-two-bytes"})
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
