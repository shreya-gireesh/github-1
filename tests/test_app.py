"""
Tests for the Mergington High School Activities API
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self):
        """Test that get_activities returns all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_participants_are_emails(self):
        """Test that participant entries are email addresses"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            for participant in activity_data["participants"]:
                assert "@" in participant
                assert ".edu" in participant


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self):
        """Test successfully signing up a new participant"""
        response = client.post(
            "/activities/Basketball%20Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_returns_success_message(self):
        """Test that signup returns appropriate success message"""
        response = client.post(
            "/activities/Soccer%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "test@mergington.edu" in data["message"]

    def test_signup_nonexistent_activity_returns_404(self):
        """Test signing up for a non-existent activity returns 404"""
        response = client.post(
            "/activities/NonExistentClub/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_participant_returns_400(self):
        """Test signing up with duplicate email returns 400"""
        # First signup
        response1 = client.post(
            "/activities/Art%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200

        # Try to signup again
        response2 = client.post(
            "/activities/Art%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_updates_participant_list(self):
        """Test that signup updates the participant list"""
        email = "verify@mergington.edu"
        activity_name = "Drama Club"

        # Get activities before signup
        before = client.get("/activities").json()
        before_count = len(before[activity_name]["participants"])

        # Signup
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        )
        assert response.status_code == 200

        # Get activities after signup
        after = client.get("/activities").json()
        after_count = len(after[activity_name]["participants"])

        assert after_count == before_count + 1
        assert email in after[activity_name]["participants"]


class TestUnregisterEndpoint:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant_success(self):
        """Test successfully unregistering an existing participant"""
        # First signup
        email = "tounregister@mergington.edu"
        client.post("/activities/Math%20Club/signup?email=tounregister@mergington.edu")

        # Then unregister
        response = client.post(
            "/activities/Math%20Club/unregister?email=tounregister@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_returns_success_message(self):
        """Test that unregister returns appropriate success message"""
        email = "unreg@mergington.edu"
        client.post("/activities/Debate%20Team/signup?email=unreg@mergington.edu")

        response = client.post(
            "/activities/Debate%20Team/unregister?email=unreg@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "unreg@mergington.edu" in data["message"]

    def test_unregister_nonexistent_activity_returns_404(self):
        """Test unregistering from non-existent activity returns 404"""
        response = client.post(
            "/activities/NonExistentClub/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_non_participant_returns_400(self):
        """Test unregistering a non-participant returns 400"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=notamember@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_updates_participant_list(self):
        """Test that unregister removes participant from list"""
        email = "todelete@mergington.edu"
        activity_name = "Programming Class"

        # Signup first
        client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        )

        # Get participants before unregister
        before = client.get("/activities").json()
        assert email in before[activity_name]["participants"]

        # Unregister
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/unregister?email={email}"
        )
        assert response.status_code == 200

        # Get participants after unregister
        after = client.get("/activities").json()
        assert email not in after[activity_name]["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
