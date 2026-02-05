from fastapi.testclient import TestClient

from src.app import app, activities


client = TestClient(app)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 302, 307, 308)
    assert "/static/index.html" in response.headers.get("location", "")


def test_get_activities_returns_all():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    # Should at least contain Chess Club and Programming Class
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_signup_for_activity_success_and_idempotency_reset():
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Ensure clean state
    if email in activities[activity_name]["participants"]:
        activities[activity_name]["participants"].remove(email)

    # First signup should succeed
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert response.status_code == 200
    result = response.json()
    assert f"Signed up {email} for {activity_name}" in result["message"]
    assert email in activities[activity_name]["participants"]

    # Second signup with same email should fail with 400
    response_dup = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert response_dup.status_code == 400
    error = response_dup.json()
    assert error["detail"] == "Student already signed up for this activity"


def test_signup_for_missing_activity():
    response = client.post("/activities/Nonexistent Activity/signup", params={"email": "test@mergington.edu"})
    assert response.status_code == 404
    error = response.json()
    assert error["detail"] == "Activity not found"


def test_unregister_from_activity_success_and_errors():
    activity_name = "Programming Class"
    email = "tempstudent@mergington.edu"

    # Make sure the student is registered first
    if email not in activities[activity_name]["participants"]:
        resp_signup = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        assert resp_signup.status_code == 200

    # Successful unregister
    response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )
    assert response.status_code == 200
    result = response.json()
    assert f"Removed {email} from {activity_name}" in result["message"]
    assert email not in activities[activity_name]["participants"]

    # Unregistering again should return 404 (not registered)
    response_not_registered = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )
    assert response_not_registered.status_code == 404
    error = response_not_registered.json()
    assert error["detail"] == "Student is not registered for this activity"


def test_unregister_from_missing_activity():
    response = client.delete(
        "/activities/Nonexistent Activity/participants", params={"email": "ghost@mergington.edu"}
    )
    assert response.status_code == 404
    error = response.json()
    assert error["detail"] == "Activity not found"
