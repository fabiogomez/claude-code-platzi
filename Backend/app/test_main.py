import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from app.main import app, get_course_service, get_rating_service
from app.services.course_service import CourseService
from app.services.rating_service import RatingService


# Mock data according to the contracts
MOCK_COURSES_LIST = [
    {
        "id": 1,
        "name": "Curso de React",
        "description": "Aprende React desde cero",
        "thumbnail": "https://via.placeholder.com/150",
        "slug": "curso-de-react",
        "average_rating": 4.5,
        "ratings_count": 2
    },
    {
        "id": 2,
        "name": "Curso de Python",
        "description": "Domina Python paso a paso",
        "thumbnail": "https://via.placeholder.com/200",
        "slug": "curso-de-python",
        "average_rating": 4.0,
        "ratings_count": 2
    }
]

MOCK_COURSE_DETAIL = {
    "id": 1,
    "name": "Curso de React",
    "description": "Aprende React desde cero",
    "thumbnail": "https://via.placeholder.com/150",
    "slug": "curso-de-react",
    "teacher_id": [1, 2],
    "classes": [
        {
            "id": 1,
            "name": "Introduccion a React",
            "description": "Conceptos basicos de React",
            "slug": "introduccion-a-react"
        },
        {
            "id": 2,
            "name": "Componentes en React",
            "description": "Aprende a crear componentes",
            "slug": "componentes-en-react"
        }
    ],
    "average_rating": 4.5,
    "ratings_count": 2
}

MOCK_RATING = {
    "id": 1,
    "course_id": 1,
    "user_identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "score": 5,
    "comment": "Excellent course!",
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00"
}

MOCK_RATINGS_LIST = [
    {
        "id": 1,
        "course_id": 1,
        "user_identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "score": 5,
        "comment": "Excellent course!",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00"
    },
    {
        "id": 2,
        "course_id": 1,
        "user_identifier": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "score": 4,
        "comment": None,
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00"
    }
]

MOCK_RATING_STATS = {
    "average_rating": 4.5,
    "ratings_count": 2
}


@pytest.fixture
def mock_course_service():
    """Create a mock CourseService for testing"""
    return Mock(spec=CourseService)


@pytest.fixture
def mock_rating_service():
    """Create a mock RatingService for testing"""
    return Mock(spec=RatingService)


@pytest.fixture
def client(mock_course_service):
    """Create test client with mocked CourseService dependency"""

    def get_mock_course_service():
        return mock_course_service

    # Override the dependency
    app.dependency_overrides[get_course_service] = get_mock_course_service

    # Create test client
    client = TestClient(app)

    yield client

    # Clean up after test
    app.dependency_overrides.clear()


@pytest.fixture
def rating_client(mock_course_service, mock_rating_service):
    """Create test client with both mocked CourseService and RatingService"""

    def get_mock_course_service():
        return mock_course_service

    def get_mock_rating_service():
        return mock_rating_service

    app.dependency_overrides[get_course_service] = get_mock_course_service
    app.dependency_overrides[get_rating_service] = get_mock_rating_service

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_returns_welcome_message(self, client):
        """Test that root endpoint returns expected welcome message"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Bienvenido a Platziflix API"}


class TestHealthEndpoint:
    """Tests for the health check endpoint"""

    def test_health_endpoint_structure(self, client):
        """Test that health endpoint returns expected structure"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()

        # Verify required fields are present
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "database" in data

        # Verify field types
        assert isinstance(data["status"], str)
        assert isinstance(data["service"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["database"], bool)


class TestCoursesEndpoints:
    """Tests for courses related endpoints"""

    def test_get_all_courses_success(self, client, mock_course_service):
        """Test GET /courses returns list of courses matching contract"""
        # Configure mock
        mock_course_service.get_all_courses.return_value = MOCK_COURSES_LIST

        response = client.get("/courses")
        assert response.status_code == 200

        data = response.json()

        # Verify response is a list
        assert isinstance(data, list)
        assert len(data) == 2

        # Verify each course has required fields according to contract
        for course in data:
            assert "id" in course
            assert "name" in course
            assert "description" in course
            assert "thumbnail" in course
            assert "slug" in course
            assert "average_rating" in course
            assert "ratings_count" in course

            # Verify field types
            assert isinstance(course["id"], int)
            assert isinstance(course["name"], str)
            assert isinstance(course["description"], str)
            assert isinstance(course["thumbnail"], str)
            assert isinstance(course["slug"], str)
            assert isinstance(course["average_rating"], (int, float))
            assert isinstance(course["ratings_count"], int)

        # Verify mock was called
        mock_course_service.get_all_courses.assert_called_once()

    def test_get_all_courses_empty_list(self, client, mock_course_service):
        """Test GET /courses when no courses exist"""
        # Configure mock to return empty list
        mock_course_service.get_all_courses.return_value = []

        response = client.get("/courses")
        assert response.status_code == 200
        assert response.json() == []

        mock_course_service.get_all_courses.assert_called_once()

    def test_get_course_by_slug_success(self, client, mock_course_service):
        """Test GET /courses/{slug} returns course details matching contract"""
        # Configure mock
        mock_course_service.get_course_by_slug.return_value = MOCK_COURSE_DETAIL

        response = client.get("/courses/curso-de-react")
        assert response.status_code == 200

        data = response.json()

        # Verify required fields according to contract
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "thumbnail" in data
        assert "slug" in data
        assert "teacher_id" in data
        assert "classes" in data
        assert "average_rating" in data
        assert "ratings_count" in data

        # Verify field types
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["description"], str)
        assert isinstance(data["thumbnail"], str)
        assert isinstance(data["slug"], str)
        assert isinstance(data["teacher_id"], list)
        assert isinstance(data["classes"], list)
        assert isinstance(data["average_rating"], (int, float))
        assert isinstance(data["ratings_count"], int)

        # Verify teacher_id contains integers
        for teacher_id in data["teacher_id"]:
            assert isinstance(teacher_id, int)

        # Verify classes structure
        for class_item in data["classes"]:
            assert "id" in class_item
            assert "name" in class_item
            assert "description" in class_item
            assert "slug" in class_item

            assert isinstance(class_item["id"], int)
            assert isinstance(class_item["name"], str)
            assert isinstance(class_item["description"], str)
            assert isinstance(class_item["slug"], str)

        # Verify mock was called with correct slug
        mock_course_service.get_course_by_slug.assert_called_once_with("curso-de-react")

    def test_get_course_by_slug_not_found(self, client, mock_course_service):
        """Test GET /courses/{slug} when course doesn't exist"""
        # Configure mock to return None
        mock_course_service.get_course_by_slug.return_value = None

        response = client.get("/courses/nonexistent-course")
        assert response.status_code == 404
        assert response.json() == {"detail": "Course not found"}

        mock_course_service.get_course_by_slug.assert_called_once_with("nonexistent-course")

    def test_get_course_by_slug_with_special_characters(self, client, mock_course_service):
        """Test GET /courses/{slug} with special characters in slug"""
        mock_course_service.get_course_by_slug.return_value = MOCK_COURSE_DETAIL

        response = client.get("/courses/curso-de-c++")
        assert response.status_code == 200

        mock_course_service.get_course_by_slug.assert_called_once_with("curso-de-c++")


class TestContractCompliance:
    """Additional tests to ensure strict contract compliance"""

    def test_courses_list_contract_fields_only(self, client, mock_course_service):
        """Ensure GET /courses response contains only contract-specified fields"""
        mock_course_service.get_all_courses.return_value = MOCK_COURSES_LIST

        response = client.get("/courses")
        data = response.json()

        expected_fields = {"id", "name", "description", "thumbnail", "slug", "average_rating", "ratings_count"}

        for course in data:
            # Verify no extra fields beyond contract
            actual_fields = set(course.keys())
            assert actual_fields == expected_fields, f"Expected {expected_fields}, got {actual_fields}"

    def test_course_detail_contract_fields_only(self, client, mock_course_service):
        """Ensure GET /courses/{slug} response contains only contract-specified fields"""
        mock_course_service.get_course_by_slug.return_value = MOCK_COURSE_DETAIL

        response = client.get("/courses/curso-de-react")
        data = response.json()

        # Verify main course fields
        expected_course_fields = {"id", "name", "description", "thumbnail", "slug", "teacher_id", "classes", "average_rating", "ratings_count"}
        actual_course_fields = set(data.keys())
        assert actual_course_fields == expected_course_fields

        # Verify classes fields
        expected_class_fields = {"id", "name", "description", "slug"}
        for class_item in data["classes"]:
            actual_class_fields = set(class_item.keys())
            assert actual_class_fields == expected_class_fields

    def test_courses_response_data_matches_contract_examples(self, client, mock_course_service):
        """Test that response structure exactly matches contract examples"""
        mock_course_service.get_all_courses.return_value = [
            {
                "id": 1,
                "name": "Curso de React",
                "description": "Curso de React",
                "thumbnail": "https://via.placeholder.com/150",
                "slug": "curso-de-react",
                "average_rating": 4.5,
                "ratings_count": 2
            }
        ]

        response = client.get("/courses")
        data = response.json()

        # Verify the response matches the exact contract structure
        assert len(data) == 1
        course = data[0]
        assert course["id"] == 1
        assert course["name"] == "Curso de React"
        assert course["description"] == "Curso de React"
        assert course["thumbnail"] == "https://via.placeholder.com/150"
        assert course["slug"] == "curso-de-react"
        assert course["average_rating"] == 4.5
        assert course["ratings_count"] == 2


class TestRatingEndpoints:
    """Tests for rating-related endpoints"""

    def test_create_rating_success(self, rating_client, mock_rating_service):
        """Test POST /courses/{slug}/ratings creates a rating successfully"""
        mock_rating_service.create_or_update_rating.return_value = MOCK_RATING

        response = rating_client.post(
            "/courses/curso-de-react/ratings",
            json={
                "score": 5,
                "user_identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "comment": "Excellent course!"
            }
        )
        assert response.status_code == 201

        data = response.json()
        assert data["id"] == 1
        assert data["score"] == 5
        assert data["user_identifier"] == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert data["comment"] == "Excellent course!"

        mock_rating_service.create_or_update_rating.assert_called_once_with(
            "curso-de-react", 5, "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "Excellent course!"
        )

    def test_create_rating_course_not_found(self, rating_client, mock_rating_service):
        """Test POST /courses/{slug}/ratings returns 404 for nonexistent course"""
        mock_rating_service.create_or_update_rating.return_value = None

        response = rating_client.post(
            "/courses/nonexistent/ratings",
            json={
                "score": 5,
                "user_identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            }
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Course not found"}

    def test_create_rating_invalid_score_too_low(self, rating_client, mock_rating_service):
        """Test POST with score=0 returns 422 validation error"""
        response = rating_client.post(
            "/courses/curso-de-react/ratings",
            json={
                "score": 0,
                "user_identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            }
        )
        assert response.status_code == 422

    def test_create_rating_invalid_score_too_high(self, rating_client, mock_rating_service):
        """Test POST with score=6 returns 422 validation error"""
        response = rating_client.post(
            "/courses/curso-de-react/ratings",
            json={
                "score": 6,
                "user_identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            }
        )
        assert response.status_code == 422

    def test_create_rating_without_comment(self, rating_client, mock_rating_service):
        """Test POST without comment creates rating with comment=null"""
        mock_rating = {**MOCK_RATING, "comment": None}
        mock_rating_service.create_or_update_rating.return_value = mock_rating

        response = rating_client.post(
            "/courses/curso-de-react/ratings",
            json={
                "score": 5,
                "user_identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            }
        )
        assert response.status_code == 201
        assert response.json()["comment"] is None

        mock_rating_service.create_or_update_rating.assert_called_once_with(
            "curso-de-react", 5, "a1b2c3d4-e5f6-7890-abcd-ef1234567890", None
        )

    def test_get_course_ratings_success(self, rating_client, mock_rating_service):
        """Test GET /courses/{slug}/ratings returns list of ratings"""
        mock_rating_service.get_ratings_by_course.return_value = MOCK_RATINGS_LIST

        response = rating_client.get("/courses/curso-de-react/ratings")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        for rating in data:
            assert "id" in rating
            assert "course_id" in rating
            assert "user_identifier" in rating
            assert "score" in rating
            assert "comment" in rating
            assert "created_at" in rating
            assert "updated_at" in rating

        mock_rating_service.get_ratings_by_course.assert_called_once_with("curso-de-react")

    def test_get_course_ratings_not_found(self, rating_client, mock_rating_service):
        """Test GET /courses/{slug}/ratings returns 404 for nonexistent course"""
        mock_rating_service.get_ratings_by_course.return_value = None

        response = rating_client.get("/courses/nonexistent/ratings")
        assert response.status_code == 404
        assert response.json() == {"detail": "Course not found"}

    def test_get_rating_stats_success(self, rating_client, mock_rating_service):
        """Test GET /courses/{slug}/ratings/stats returns rating statistics"""
        mock_rating_service.get_rating_stats.return_value = MOCK_RATING_STATS

        response = rating_client.get("/courses/curso-de-react/ratings/stats")
        assert response.status_code == 200

        data = response.json()
        assert "average_rating" in data
        assert "ratings_count" in data
        assert isinstance(data["average_rating"], (int, float))
        assert isinstance(data["ratings_count"], int)
        assert data["average_rating"] == 4.5
        assert data["ratings_count"] == 2

        mock_rating_service.get_rating_stats.assert_called_once_with("curso-de-react")

    def test_get_rating_stats_not_found(self, rating_client, mock_rating_service):
        """Test GET /courses/{slug}/ratings/stats returns 404 for nonexistent course"""
        mock_rating_service.get_rating_stats.return_value = None

        response = rating_client.get("/courses/nonexistent/ratings/stats")
        assert response.status_code == 404
        assert response.json() == {"detail": "Course not found"}

    def test_delete_rating_success(self, rating_client, mock_rating_service):
        """Test DELETE /ratings/{id} soft-deletes a rating"""
        mock_rating_service.delete_rating.return_value = {"message": "Rating deleted successfully"}

        response = rating_client.delete(
            "/ratings/1?user_identifier=a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        )
        assert response.status_code == 200
        assert response.json() == {"message": "Rating deleted successfully"}

        mock_rating_service.delete_rating.assert_called_once_with(
            1, "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        )

    def test_delete_rating_not_found(self, rating_client, mock_rating_service):
        """Test DELETE /ratings/{id} returns 404 when not found or not authorized"""
        mock_rating_service.delete_rating.return_value = None

        response = rating_client.delete(
            "/ratings/999?user_identifier=wrong-user-identifier-value"
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Rating not found or not authorized"}


class TestCoursesWithRatings:
    """Tests to verify courses endpoints include rating fields"""

    def test_courses_list_includes_rating_fields(self, client, mock_course_service):
        """Test GET /courses includes average_rating and ratings_count"""
        mock_course_service.get_all_courses.return_value = MOCK_COURSES_LIST

        response = client.get("/courses")
        data = response.json()

        for course in data:
            assert "average_rating" in course
            assert "ratings_count" in course
            assert isinstance(course["average_rating"], (int, float))
            assert isinstance(course["ratings_count"], int)

    def test_course_detail_includes_rating_fields(self, client, mock_course_service):
        """Test GET /courses/{slug} includes average_rating and ratings_count"""
        mock_course_service.get_course_by_slug.return_value = MOCK_COURSE_DETAIL

        response = client.get("/courses/curso-de-react")
        data = response.json()

        assert "average_rating" in data
        assert "ratings_count" in data
        assert data["average_rating"] == 4.5
        assert data["ratings_count"] == 2
