from app.main import app
from starlette.testclient import TestClient

client = TestClient(app)


def test_departments_list(auth_headers):
    r = client.get("/departments/", headers=auth_headers)
    assert r.status_code == 200
    departments = r.json()
    assert isinstance(departments, list)
    # Check that we have department objects with names
    dept_names = [dept.get("name", "").lower() for dept in departments]
    assert "engineering" in dept_names
    assert "marketing" in dept_names


def test_tasks_catalog(auth_headers):
    r = client.get("/tasks-catalog/", headers=auth_headers)
    assert r.status_code == 200
    tasks = r.json()
    assert isinstance(tasks, list)
    # Check that we have task objects with categories
    task_categories = [task.get("category", "").lower() for task in tasks]
    assert "development" in task_categories
    assert "security" in task_categories
