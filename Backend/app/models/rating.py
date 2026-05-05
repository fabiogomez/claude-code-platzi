from sqlalchemy import Column, String, Text, Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from .base import BaseModel


class Rating(BaseModel):
    """
    Rating model representing user ratings for courses.
    """
    __tablename__ = 'ratings'

    __table_args__ = (
        UniqueConstraint('course_id', 'user_identifier', name='uq_rating_course_user'),
        CheckConstraint('score >= 1 AND score <= 5', name='ck_rating_score_range'),
    )

    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False, index=True)
    user_identifier = Column(String(255), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)

    # Many-to-one relationship with Course
    course = relationship("Course", back_populates="ratings")

    def __repr__(self):
        return f"<Rating(id={self.id}, course_id={self.course_id}, score={self.score})>"
