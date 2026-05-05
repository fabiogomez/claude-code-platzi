from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.course import Course
from app.models.rating import Rating


class RatingService:
    """
    Service class for handling rating-related operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def _get_course_by_slug(self, slug: str) -> Optional[Course]:
        """Look up a course by slug, filtering soft-deleted."""
        return (
            self.db.query(Course)
            .filter(Course.slug == slug)
            .filter(Course.deleted_at.is_(None))
            .first()
        )

    def create_or_update_rating(
        self, slug: str, score: int, user_identifier: str, comment: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new rating or update an existing one (upsert by course + user_identifier).

        Returns:
            Rating dict if successful, None if course not found.
        """
        course = self._get_course_by_slug(slug)
        if not course:
            return None

        existing = (
            self.db.query(Rating)
            .filter(
                Rating.course_id == course.id,
                Rating.user_identifier == user_identifier,
                Rating.deleted_at.is_(None),
            )
            .first()
        )

        if existing:
            existing.score = score
            existing.comment = comment
            self.db.commit()
            self.db.refresh(existing)
            rating = existing
        else:
            rating = Rating(
                course_id=course.id,
                user_identifier=user_identifier,
                score=score,
                comment=comment,
            )
            self.db.add(rating)
            self.db.commit()
            self.db.refresh(rating)

        return {
            "id": rating.id,
            "course_id": rating.course_id,
            "user_identifier": rating.user_identifier,
            "score": rating.score,
            "comment": rating.comment,
            "created_at": rating.created_at.isoformat(),
            "updated_at": rating.updated_at.isoformat(),
        }

    def get_ratings_by_course(self, slug: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get all ratings for a course by slug.

        Returns:
            List of rating dicts, or None if course not found.
        """
        course = self._get_course_by_slug(slug)
        if not course:
            return None

        ratings = (
            self.db.query(Rating)
            .filter(Rating.course_id == course.id, Rating.deleted_at.is_(None))
            .order_by(Rating.created_at.desc())
            .all()
        )

        return [
            {
                "id": r.id,
                "course_id": r.course_id,
                "user_identifier": r.user_identifier,
                "score": r.score,
                "comment": r.comment,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
            }
            for r in ratings
        ]

    def get_rating_stats(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Get rating statistics for a course by slug.

        Returns:
            Dict with average_rating and ratings_count, or None if course not found.
        """
        course = self._get_course_by_slug(slug)
        if not course:
            return None

        return self.get_rating_stats_for_course_id(course.id)

    def get_rating_stats_for_course_id(self, course_id: int) -> Dict[str, Any]:
        """
        Get rating statistics for a course by ID.
        Used internally by CourseService to enrich course responses.
        """
        result = (
            self.db.query(
                func.coalesce(func.avg(Rating.score), 0),
                func.count(Rating.id),
            )
            .filter(Rating.course_id == course_id, Rating.deleted_at.is_(None))
            .first()
        )

        return {
            "average_rating": round(float(result[0]), 1),
            "ratings_count": result[1],
        }

    def delete_rating(
        self, rating_id: int, user_identifier: str
    ) -> Optional[Dict[str, str]]:
        """
        Soft-delete a rating by ID and user_identifier.

        Returns:
            Success message dict, or None if not found/not authorized.
        """
        rating = (
            self.db.query(Rating)
            .filter(
                Rating.id == rating_id,
                Rating.user_identifier == user_identifier,
                Rating.deleted_at.is_(None),
            )
            .first()
        )

        if not rating:
            return None

        rating.deleted_at = datetime.utcnow()
        self.db.commit()

        return {"message": "Rating deleted successfully"}
