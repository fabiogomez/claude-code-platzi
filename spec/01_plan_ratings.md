# Plan de Implementacion: Sistema de Ratings (1-5 Estrellas) para Cursos

**Fecha:** 2026-03-30
**Branch base:** `start-zero`
**Autor:** Arquitecto de Software (Claude Opus 4.6)
**Documento previo:** `spec/PLATZIFLIX_IMPACT_ANALYSIS.md`

---

## Resumen Ejecutivo

Este plan detalla la implementacion paso a paso de un sistema de calificaciones por estrellas (1-5) para cursos en PlatziFlix. Los usuarios pueden calificar cursos y dejar comentarios opcionales sin necesidad de autenticacion -- se usa un UUID generado en el navegador y persistido en `localStorage` como identificador anonimo (`user_identifier`).

El feature se descompone en 5 fases ordenadas por dependencia:

| Fase | Descripcion | Archivos nuevos | Archivos modificados |
|------|-------------|-----------------|---------------------|
| 1 | Modelo de datos y migracion | 2 | 2 |
| 2 | Servicio y logica de negocio | 2 | 1 |
| 3 | Endpoints API y contratos | 0 | 3 |
| 4 | Tests backend | 0 | 1 |
| 5 | Frontend: tipos, componentes y paginas | 4 | 6 |

**Total:** 8 archivos nuevos, 13 archivos modificados.

---

## Fase 1: Modelo de Datos y Migracion

**Objetivo:** Crear el modelo SQLAlchemy `Rating` y la migracion Alembic correspondiente para la tabla `ratings`.

**Dependencias:** Ninguna (esta fase es la base de todo lo demas).

---

### Tarea 1.1: Crear modelo SQLAlchemy `Rating`

**Archivo a crear:** `Backend/app/models/rating.py`

**Descripcion:** Nuevo modelo que extiende `BaseModel` (hereda `id`, `created_at`, `updated_at`, `deleted_at`) siguiendo exactamente el patron de los modelos existentes (`lesson.py`, `teacher.py`).

```python
from sqlalchemy import Column, String, Text, Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from .base import BaseModel


class Rating(BaseModel):
    """
    Rating model representing user ratings for courses.
    Uses user_identifier (UUID from localStorage) instead of authentication.
    """
    __tablename__ = 'ratings'

    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False, index=True)
    user_identifier = Column(String(255), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint('course_id', 'user_identifier', name='uq_rating_course_user'),
        CheckConstraint('score >= 1 AND score <= 5', name='ck_rating_score_range'),
    )

    # Many-to-one relationship with Course
    course = relationship("Course", back_populates="ratings")

    def __repr__(self):
        return f"<Rating(id={self.id}, course_id={self.course_id}, score={self.score})>"
```

**Notas sobre convenciones seguidas:**
- Hereda de `BaseModel` (igual que `Lesson`, `Teacher`, `Course`).
- Usa `Column(Integer, ForeignKey('courses.id'), nullable=False, index=True)` -- mismo patron que `Lesson.course_id`.
- `__repr__` sigue el patron existente: `f"<ClassName(id={self.id}, ...>)"`.
- Relacion `relationship("Course", back_populates="ratings")` -- mismo patron que `Lesson.course`.

---

### Tarea 1.2: Registrar modelo en `__init__.py` y agregar relacion inversa en `Course`

**Archivo a modificar:** `Backend/app/models/__init__.py`

**Cambio:** Agregar import de `Rating` y registrarlo en `__all__`.

```python
# Import all models to make them available when importing from models package
# This ensures Alembic can detect all models for auto-generation

from .base import BaseModel, Base
from .teacher import Teacher
from .course import Course
from .lesson import Lesson
from .course_teacher import course_teachers
from .rating import Rating  # NUEVO

# Export all models for easy importing
__all__ = [
    'BaseModel',
    'Base',
    'Teacher',
    'Course',
    'Lesson',
    'course_teachers',
    'Rating',  # NUEVO
]
```

**Archivo a modificar:** `Backend/app/models/course.py`

**Cambio:** Agregar relacion `ratings` en el modelo `Course`.

Agregar al final de las relaciones existentes (despues de `lessons`):

```python
    # One-to-many relationship with Rating
    ratings = relationship(
        "Rating",
        back_populates="course",
        cascade="all, delete-orphan"
    )
```

El archivo completo queda:

```python
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from .base import BaseModel


class Course(BaseModel):
    """
    Course model representing online courses in the platform.
    """
    __tablename__ = 'courses'

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    thumbnail = Column(String(500), nullable=False)  # URL to thumbnail image
    slug = Column(String(255), nullable=False, unique=True, index=True)

    # Many-to-many relationship with Teacher
    teachers = relationship(
        "Teacher",
        secondary="course_teachers",
        back_populates="courses"
    )

    # One-to-many relationship with Lesson
    lessons = relationship(
        "Lesson",
        back_populates="course",
        cascade="all, delete-orphan"
    )

    # One-to-many relationship with Rating
    ratings = relationship(
        "Rating",
        back_populates="course",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Course(id={self.id}, name='{self.name}', slug='{self.slug}')>"
```

---

### Tarea 1.3: Generar migracion Alembic

**Comando:**

```bash
make create-migration
# Mensaje: "Add ratings table with score, user_identifier, and course relationship"
```

Esto ejecuta internamente:

```bash
docker-compose exec api bash -c "cd /app && uv run alembic -c app/alembic.ini revision --autogenerate -m 'Add ratings table with score, user_identifier, and course relationship'"
```

**Archivo generado:** `Backend/app/alembic/versions/<hash>_add_ratings_table_with_score_user_identifier_.py`

La migracion autogenerada deberia contener (verificar despues de generar):

```python
def upgrade() -> None:
    op.create_table(
        'ratings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('user_identifier', sa.String(length=255), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'user_identifier', name='uq_rating_course_user'),
        sa.CheckConstraint('score >= 1 AND score <= 5', name='ck_rating_score_range'),
    )
    op.create_index(op.f('ix_ratings_id'), 'ratings', ['id'], unique=False)
    op.create_index(op.f('ix_ratings_course_id'), 'ratings', ['course_id'], unique=False)
    op.create_index(op.f('ix_ratings_user_identifier'), 'ratings', ['user_identifier'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ratings_user_identifier'), table_name='ratings')
    op.drop_index(op.f('ix_ratings_course_id'), table_name='ratings')
    op.drop_index(op.f('ix_ratings_id'), table_name='ratings')
    op.drop_table('ratings')
```

**Despues de generar, aplicar:**

```bash
make migrate
```

---

### Tarea 1.4: Agregar ratings al seed de datos

**Archivo a modificar:** `Backend/app/db/seed.py`

**Cambio:** Importar `Rating` y agregar datos de ejemplo despues de la creacion de lessons.

Agregar al import existente:

```python
from app.models import Teacher, Course, Lesson, course_teachers, Rating
```

Agregar al final del bloque `try`, despues del commit de lessons y antes del `print`:

```python
        # Create sample ratings
        ratings_data = [
            # Ratings for React course
            {
                "course": course1,
                "user_identifier": "550e8400-e29b-41d4-a716-446655440001",
                "score": 5,
                "comment": "Excelente curso, muy bien explicado",
            },
            {
                "course": course1,
                "user_identifier": "550e8400-e29b-41d4-a716-446655440002",
                "score": 4,
                "comment": "Muy bueno, pero podria tener mas ejercicios",
            },
            # Ratings for Python course
            {
                "course": course2,
                "user_identifier": "550e8400-e29b-41d4-a716-446655440001",
                "score": 5,
                "comment": None,
            },
            {
                "course": course2,
                "user_identifier": "550e8400-e29b-41d4-a716-446655440003",
                "score": 3,
                "comment": "Buen contenido, pero algo basico",
            },
            # Rating for JavaScript course
            {
                "course": course3,
                "user_identifier": "550e8400-e29b-41d4-a716-446655440002",
                "score": 4,
                "comment": "Me gusto mucho el enfoque moderno",
            },
        ]

        for rating_data in ratings_data:
            rating = Rating(
                course_id=rating_data["course"].id,
                user_identifier=rating_data["user_identifier"],
                score=rating_data["score"],
                comment=rating_data["comment"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(rating)

        db.commit()
```

Actualizar el print final:

```python
        print("✅ Sample data created successfully!")
        print(f"   - Created {len([teacher1, teacher2, teacher3])} teachers")
        print(f"   - Created {len([course1, course2, course3])} courses")
        print(f"   - Created {len(lessons_data)} lessons")
        print(f"   - Created {len(ratings_data)} ratings")
```

Actualizar `clear_all_data()` -- agregar la eliminacion de ratings ANTES de eliminar courses (por la FK):

```python
    def clear_all_data():
        """Clear all data from the database."""
        db: Session = SessionLocal()

        try:
            # Delete in reverse order to avoid foreign key constraints
            db.query(Rating).delete()  # NUEVO - antes de Course
            db.query(Lesson).delete()
            db.execute(course_teachers.delete())
            db.query(Course).delete()
            db.query(Teacher).delete()
            db.commit()

            print("✅ All data cleared successfully!")

        except Exception as e:
            db.rollback()
            print(f"❌ Error clearing data: {e}")
            raise
        finally:
            db.close()
```

Agregar `Rating` tambien al import de `clear_all_data` (ya esta en el import global del archivo).

---

### Criterio de verificacion de Fase 1

1. La migracion se ejecuta sin errores: `make migrate`
2. La tabla `ratings` existe en PostgreSQL con las columnas, constraints e indices correctos
3. `make seed-fresh` crea los ratings de ejemplo sin errores
4. Verificar con SQL directo: `SELECT COUNT(*) FROM ratings` retorna 5

---

## Fase 2: Servicio de Ratings (Logica de Negocio)

**Objetivo:** Crear `RatingService` con toda la logica de negocio para CRUD de ratings y calculo de estadisticas.

**Dependencias:** Fase 1 completada (modelo `Rating` existe y la migracion esta aplicada).

---

### Tarea 2.1: Crear Pydantic schemas para ratings

**Archivo a crear:** `Backend/app/schemas/__init__.py`

```python
from .rating import RatingCreate, RatingResponse, RatingStats

__all__ = ['RatingCreate', 'RatingResponse', 'RatingStats']
```

**Archivo a crear:** `Backend/app/schemas/rating.py`

**Descripcion:** Schemas Pydantic para validacion de entrada y tipado de respuestas. El proyecto no usa Pydantic response models en los endpoints existentes (los endpoints retornan `dict`), pero introducimos schemas aqui para validar el input del POST de ratings, que es el primer endpoint que recibe datos del usuario.

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RatingCreate(BaseModel):
    """Schema for creating or updating a rating."""
    score: int = Field(..., ge=1, le=5, description="Rating score from 1 to 5")
    user_identifier: str = Field(
        ...,
        min_length=36,
        max_length=255,
        description="UUID from client localStorage"
    )
    comment: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional comment about the course"
    )


class RatingResponse(BaseModel):
    """Schema for rating in API responses."""
    id: int
    course_id: int
    user_identifier: str
    score: int
    comment: Optional[str]
    created_at: datetime
    updated_at: datetime


class RatingStats(BaseModel):
    """Schema for aggregated rating statistics."""
    average_rating: float = Field(..., description="Average score rounded to 1 decimal")
    ratings_count: int = Field(..., description="Total number of ratings")
```

---

### Tarea 2.2: Crear `RatingService`

**Archivo a crear:** `Backend/app/services/rating_service.py`

**Descripcion:** Servicio que encapsula toda la logica de negocio para ratings. Sigue exactamente el patron de `CourseService`: recibe `db: Session` en el constructor, retorna dicts/listas.

```python
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.rating import Rating
from app.models.course import Course


class RatingService:
    """
    Service class for handling rating-related operations.
    Implements CRUD for course ratings and statistics calculation.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_or_update_rating(self, slug: str, score: int, user_identifier: str, comment: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new rating or update an existing one for a course.
        Uses upsert logic based on (course_id, user_identifier) unique constraint.

        Args:
            slug: The course slug
            score: Rating score (1-5)
            user_identifier: UUID from client localStorage
            comment: Optional comment

        Returns:
            Rating dictionary, or None if course not found
        """
        # Find the course by slug
        course = (
            self.db.query(Course)
            .filter(Course.slug == slug)
            .filter(Course.deleted_at.is_(None))
            .first()
        )

        if not course:
            return None

        # Check if rating already exists for this user and course
        existing_rating = (
            self.db.query(Rating)
            .filter(Rating.course_id == course.id)
            .filter(Rating.user_identifier == user_identifier)
            .filter(Rating.deleted_at.is_(None))
            .first()
        )

        if existing_rating:
            # Update existing rating
            existing_rating.score = score
            existing_rating.comment = comment
            self.db.commit()
            self.db.refresh(existing_rating)
            rating = existing_rating
        else:
            # Create new rating
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
        Get all ratings for a course.

        Args:
            slug: The course slug

        Returns:
            List of rating dictionaries, or None if course not found
        """
        course = (
            self.db.query(Course)
            .filter(Course.slug == slug)
            .filter(Course.deleted_at.is_(None))
            .first()
        )

        if not course:
            return None

        ratings = (
            self.db.query(Rating)
            .filter(Rating.course_id == course.id)
            .filter(Rating.deleted_at.is_(None))
            .order_by(Rating.created_at.desc())
            .all()
        )

        return [
            {
                "id": rating.id,
                "course_id": rating.course_id,
                "user_identifier": rating.user_identifier,
                "score": rating.score,
                "comment": rating.comment,
                "created_at": rating.created_at.isoformat(),
                "updated_at": rating.updated_at.isoformat(),
            }
            for rating in ratings
        ]

    def get_rating_stats(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Get aggregated rating statistics for a course.

        Args:
            slug: The course slug

        Returns:
            Stats dictionary with average_rating and ratings_count, or None if course not found
        """
        course = (
            self.db.query(Course)
            .filter(Course.slug == slug)
            .filter(Course.deleted_at.is_(None))
            .first()
        )

        if not course:
            return None

        result = (
            self.db.query(
                func.coalesce(func.avg(Rating.score), 0).label("average_rating"),
                func.count(Rating.id).label("ratings_count"),
            )
            .filter(Rating.course_id == course.id)
            .filter(Rating.deleted_at.is_(None))
            .first()
        )

        return {
            "average_rating": round(float(result.average_rating), 1),
            "ratings_count": result.ratings_count,
        }

    def delete_rating(self, rating_id: int, user_identifier: str) -> Optional[Dict[str, str]]:
        """
        Soft-delete a rating. Only the owner (same user_identifier) can delete.

        Args:
            rating_id: The rating ID
            user_identifier: UUID from client localStorage

        Returns:
            Success message dict, or None if not found/not authorized
        """
        from datetime import datetime

        rating = (
            self.db.query(Rating)
            .filter(Rating.id == rating_id)
            .filter(Rating.user_identifier == user_identifier)
            .filter(Rating.deleted_at.is_(None))
            .first()
        )

        if not rating:
            return None

        rating.deleted_at = datetime.utcnow()
        self.db.commit()

        return {"message": "Rating deleted successfully"}

    def get_rating_stats_for_course_id(self, course_id: int) -> Dict[str, Any]:
        """
        Get aggregated rating statistics by course_id (internal use).
        Used by CourseService to enrich course listings.

        Args:
            course_id: The course ID

        Returns:
            Stats dictionary with average_rating and ratings_count
        """
        result = (
            self.db.query(
                func.coalesce(func.avg(Rating.score), 0).label("average_rating"),
                func.count(Rating.id).label("ratings_count"),
            )
            .filter(Rating.course_id == course_id)
            .filter(Rating.deleted_at.is_(None))
            .first()
        )

        return {
            "average_rating": round(float(result.average_rating), 1),
            "ratings_count": result.ratings_count,
        }
```

---

### Tarea 2.3: Registrar `RatingService` en el modulo de servicios

**Archivo a modificar:** `Backend/app/services/__init__.py`

```python
from .course_service import CourseService
from .rating_service import RatingService

__all__ = ['CourseService', 'RatingService']
```

---

### Tarea 2.4: Modificar `CourseService` para incluir rating stats

**Archivo a modificar:** `Backend/app/services/course_service.py`

**Cambio:** Agregar `average_rating` y `ratings_count` a las respuestas de `get_all_courses()` y `get_course_by_slug()` usando una subquery SQL eficiente en lugar de cargar todos los ratings en memoria.

```python
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.teacher import Teacher
from app.models.rating import Rating


class CourseService:
    """
    Service class for handling course-related operations.
    Implements the contract specifications for course endpoints.
    """

    def __init__(self, db: Session):
        self.db = db

    def _get_rating_stats(self, course_id: int) -> Dict[str, Any]:
        """
        Get rating statistics for a course using an efficient aggregate query.
        """
        result = (
            self.db.query(
                func.coalesce(func.avg(Rating.score), 0).label("average_rating"),
                func.count(Rating.id).label("ratings_count"),
            )
            .filter(Rating.course_id == course_id)
            .filter(Rating.deleted_at.is_(None))
            .first()
        )

        return {
            "average_rating": round(float(result.average_rating), 1),
            "ratings_count": result.ratings_count,
        }

    def get_all_courses(self) -> List[Dict[str, Any]]:
        """
        Get all courses with basic information (no teachers or lessons).

        Returns:
            List of course dictionaries with: id, name, description, thumbnail, slug,
            average_rating, ratings_count
        """
        courses = self.db.query(Course).filter(Course.deleted_at.is_(None)).all()

        return [
            {
                "id": course.id,
                "name": course.name,
                "description": course.description,
                "thumbnail": course.thumbnail,
                "slug": course.slug,
                **self._get_rating_stats(course.id),
            }
            for course in courses
        ]

    def get_course_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Get course details by slug including teachers and lessons.

        Args:
            slug: The course slug

        Returns:
            Course dictionary with teachers, lessons, and rating stats, or None if not found
        """
        course = (
            self.db.query(Course)
            .options(
                joinedload(Course.teachers),
                joinedload(Course.lessons)
            )
            .filter(Course.slug == slug)
            .filter(Course.deleted_at.is_(None))
            .first()
        )

        if not course:
            return None

        return {
            "id": course.id,
            "name": course.name,
            "description": course.description,
            "thumbnail": course.thumbnail,
            "slug": course.slug,
            "teacher_id": [teacher.id for teacher in course.teachers],
            "classes": [
                {
                    "id": lesson.id,
                    "name": lesson.name,
                    "description": lesson.description,
                    "slug": lesson.slug
                }
                for lesson in course.lessons
                if lesson.deleted_at is None
            ],
            **self._get_rating_stats(course.id),
        }
```

**Nota sobre performance:** El metodo `_get_rating_stats` ejecuta una query `AVG/COUNT` por curso. Para la escala actual (3 cursos) esto es aceptable. Si la cantidad de cursos crece significativamente (100+), se deberia considerar:
- Una subquery lateral en la query principal de `get_all_courses`
- O campos precalculados `average_rating`/`ratings_count` en la tabla `courses` con trigger o actualizacion en el servicio de ratings

---

### Criterio de verificacion de Fase 2

1. El modulo `app.services.rating_service` se puede importar sin errores
2. `CourseService.get_all_courses()` retorna dicts con campos `average_rating` y `ratings_count`
3. `CourseService.get_course_by_slug("curso-de-react")` incluye `average_rating` y `ratings_count`
4. `RatingService.get_rating_stats("curso-de-react")` retorna `{"average_rating": 4.5, "ratings_count": 2}` (con seed data)

---

## Fase 3: Endpoints API

**Objetivo:** Exponer la funcionalidad de ratings via endpoints REST en `main.py`, siguiendo el patron de dependency injection existente.

**Dependencias:** Fase 2 completada.

---

### Tarea 3.1: Agregar endpoints de ratings en `main.py`

**Archivo a modificar:** `Backend/app/main.py`

**Descripcion:** Agregar 4 nuevos endpoints y la factory de dependency injection para `RatingService`. Se sigue el patron exacto del `get_course_service` existente.

```python
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.base import engine, get_db
from app.services.course_service import CourseService
from app.services.rating_service import RatingService
from app.schemas.rating import RatingCreate

app = FastAPI(title=settings.project_name, version=settings.version)


def get_course_service(db: Session = Depends(get_db)) -> CourseService:
    """
    Dependency to get CourseService instance
    """
    return CourseService(db)


def get_rating_service(db: Session = Depends(get_db)) -> RatingService:
    """
    Dependency to get RatingService instance
    """
    return RatingService(db)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Bienvenido a Platziflix API"}


@app.get("/health")
def health() -> dict[str, str | bool | int]:
    """
    Health check endpoint that verifies:
    - Service status
    - Database connectivity
    """
    health_status = {
        "status": "ok",
        "service": settings.project_name,
        "version": settings.version,
        "database": False,
    }

    # Check database connectivity and verify migration
    try:
        with engine.connect() as connection:
            # Execute COUNT on courses table to verify migration was executed
            result = connection.execute(text("SELECT COUNT(*) FROM courses"))
            row = result.fetchone()
            if row:
                count = row[0]
                health_status["database"] = True
                health_status["courses_count"] = count
            else:
                health_status["database"] = True
                health_status["courses_count"] = 0
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["database_error"] = str(e)

    return health_status


@app.get("/courses")
def get_courses(course_service: CourseService = Depends(get_course_service)) -> list:
    """
    Get all courses.
    Returns a list of courses with basic information: id, name, description, thumbnail, slug,
    average_rating, ratings_count
    """
    return course_service.get_all_courses()


@app.get("/courses/{slug}")
def get_course_by_slug(slug: str, course_service: CourseService = Depends(get_course_service)) -> dict:
    """
    Get course details by slug.
    Returns course information including teachers, classes, and rating statistics.
    """
    course = course_service.get_course_by_slug(slug)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return course


# --- Rating endpoints ---


@app.post("/courses/{slug}/ratings", status_code=201)
def create_or_update_rating(
    slug: str,
    rating_data: RatingCreate,
    rating_service: RatingService = Depends(get_rating_service),
) -> dict:
    """
    Create or update a rating for a course.
    If the user_identifier already has a rating for this course, it updates it.
    """
    result = rating_service.create_or_update_rating(
        slug=slug,
        score=rating_data.score,
        user_identifier=rating_data.user_identifier,
        comment=rating_data.comment,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Course not found")

    return result


@app.get("/courses/{slug}/ratings")
def get_course_ratings(
    slug: str,
    rating_service: RatingService = Depends(get_rating_service),
) -> list:
    """
    Get all ratings for a course.
    Returns a list of ratings ordered by most recent first.
    """
    result = rating_service.get_ratings_by_course(slug)

    if result is None:
        raise HTTPException(status_code=404, detail="Course not found")

    return result


@app.get("/courses/{slug}/ratings/stats")
def get_course_rating_stats(
    slug: str,
    rating_service: RatingService = Depends(get_rating_service),
) -> dict:
    """
    Get aggregated rating statistics for a course.
    Returns average_rating and ratings_count.
    """
    result = rating_service.get_rating_stats(slug)

    if result is None:
        raise HTTPException(status_code=404, detail="Course not found")

    return result


@app.delete("/ratings/{rating_id}")
def delete_rating(
    rating_id: int,
    user_identifier: str,
    rating_service: RatingService = Depends(get_rating_service),
) -> dict:
    """
    Soft-delete a rating. Only the owner (matching user_identifier) can delete.
    user_identifier is passed as a query parameter.
    """
    result = rating_service.delete_rating(rating_id, user_identifier)

    if not result:
        raise HTTPException(status_code=404, detail="Rating not found or not authorized")

    return result
```

**Notas importantes:**
- `POST /courses/{slug}/ratings` usa `status_code=201` para indicar creacion.
- `DELETE /ratings/{rating_id}` recibe `user_identifier` como query parameter (no path) ya que no hay auth -- el user_identifier actua como token de propiedad.
- La ruta de stats es `/courses/{slug}/ratings/stats` y debe declararse DESPUES de `/courses/{slug}/ratings` para que FastAPI no confunda `stats` con un slug.

---

### Tarea 3.2: Actualizar contratos de API

**Archivo a modificar:** `Backend/specs/00_contracts.md`

**Cambio:** Agregar la entidad Rating y los nuevos endpoints al final del documento, y actualizar los contratos existentes de Course para incluir rating stats.

Agregar al final del archivo:

```markdown

- Rating
```json
{
    "id": 1,
    "course_id": 1,
    "user_identifier": "550e8400-e29b-41d4-a716-446655440001",
    "score": 5,
    "comment": "Excelente curso",
    "created_at": "2021-01-01T00:00:00",
    "updated_at": "2021-01-01T00:00:00"
}
```

### Endpoints de Ratings

- POST /courses/:slug/ratings -> Crear o actualizar un rating
  - Body:
```json
{
    "score": 5,
    "user_identifier": "550e8400-e29b-41d4-a716-446655440001",
    "comment": "Excelente curso"
}
```
  - Response (201):
```json
{
    "id": 1,
    "course_id": 1,
    "user_identifier": "550e8400-e29b-41d4-a716-446655440001",
    "score": 5,
    "comment": "Excelente curso",
    "created_at": "2021-01-01T00:00:00",
    "updated_at": "2021-01-01T00:00:00"
}
```

- GET /courses/:slug/ratings -> Listar ratings de un curso
```json
[
    {
        "id": 1,
        "course_id": 1,
        "user_identifier": "550e8400-e29b-41d4-a716-446655440001",
        "score": 5,
        "comment": "Excelente curso",
        "created_at": "2021-01-01T00:00:00",
        "updated_at": "2021-01-01T00:00:00"
    }
]
```

- GET /courses/:slug/ratings/stats -> Estadisticas de rating de un curso
```json
{
    "average_rating": 4.5,
    "ratings_count": 10
}
```

- DELETE /ratings/:id?user_identifier=UUID -> Eliminar rating propio
```json
{
    "message": "Rating deleted successfully"
}
```
```

Tambien actualizar los contratos existentes de `GET /courses` y `GET /courses/:slug` para incluir `average_rating` y `ratings_count`:

En la seccion de `GET /courses`:
```json
[
    {
        "id": 1,
        "name": "Curso de React",
        "description": "Curso de React",
        "thumbnail": "https://via.placeholder.com/150",
        "slug": "curso-de-react",
        "average_rating": 4.5,
        "ratings_count": 10
    }
]
```

En la seccion de `GET /courses/:slug`:
```json
{
    "id": 1,
    "name": "Curso de React",
    "description": "Curso de React",
    "thumbnail": "https://via.placeholder.com/150",
    "slug": "curso-de-react",
    "teacher_id": [1, 2, 3],
    "classes": [...],
    "average_rating": 4.5,
    "ratings_count": 10
}
```

---

### Criterio de verificacion de Fase 3

1. `GET /courses` retorna cursos con `average_rating` y `ratings_count`
2. `GET /courses/curso-de-react` incluye `average_rating: 4.5` y `ratings_count: 2`
3. `POST /courses/curso-de-react/ratings` con body valido retorna 201 y el rating creado
4. `POST /courses/curso-de-react/ratings` con el mismo `user_identifier` actualiza el rating existente
5. `POST /courses/nonexistent/ratings` retorna 404
6. `POST` con `score: 0` o `score: 6` retorna 422 (Pydantic validation)
7. `GET /courses/curso-de-react/ratings` retorna la lista de ratings
8. `GET /courses/curso-de-react/ratings/stats` retorna el promedio y conteo
9. `DELETE /ratings/{id}?user_identifier=UUID` con el UUID correcto retorna 200
10. `DELETE /ratings/{id}?user_identifier=wrong-uuid` retorna 404
11. La documentacion en `/docs` muestra los nuevos endpoints correctamente

---

## Fase 4: Tests Backend

**Objetivo:** Agregar tests unitarios para los nuevos endpoints y verificar la integracion con los mocks.

**Dependencias:** Fase 3 completada.

---

### Tarea 4.1: Agregar tests para endpoints de ratings

**Archivo a modificar:** `Backend/app/test_main.py`

**Descripcion:** Agregar nuevas clases de test siguiendo el patron existente: mock del servicio, override de dependency, assertions sobre status code y estructura de respuesta.

Agregar al inicio del archivo (imports):

```python
from app.services.rating_service import RatingService
from app.main import get_rating_service
```

Agregar nuevo mock data despues de `MOCK_COURSE_DETAIL`:

```python
MOCK_RATING = {
    "id": 1,
    "course_id": 1,
    "user_identifier": "550e8400-e29b-41d4-a716-446655440001",
    "score": 5,
    "comment": "Excelente curso",
    "created_at": "2021-01-01T00:00:00",
    "updated_at": "2021-01-01T00:00:00",
}

MOCK_RATINGS_LIST = [
    MOCK_RATING,
    {
        "id": 2,
        "course_id": 1,
        "user_identifier": "550e8400-e29b-41d4-a716-446655440002",
        "score": 4,
        "comment": "Muy bueno",
        "created_at": "2021-01-02T00:00:00",
        "updated_at": "2021-01-02T00:00:00",
    },
]

MOCK_RATING_STATS = {
    "average_rating": 4.5,
    "ratings_count": 2,
}
```

Agregar nuevos fixtures:

```python
@pytest.fixture
def mock_rating_service():
    """Create a mock RatingService for testing"""
    return Mock(spec=RatingService)


@pytest.fixture
def rating_client(mock_rating_service, mock_course_service):
    """Create test client with mocked RatingService and CourseService dependencies"""

    def get_mock_course_service():
        return mock_course_service

    def get_mock_rating_service():
        return mock_rating_service

    # Override dependencies
    app.dependency_overrides[get_course_service] = get_mock_course_service
    app.dependency_overrides[get_rating_service] = get_mock_rating_service

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()
```

Agregar nuevas clases de test:

```python
class TestRatingEndpoints:
    """Tests for rating-related endpoints"""

    def test_create_rating_success(self, rating_client, mock_rating_service):
        """Test POST /courses/{slug}/ratings creates a rating"""
        mock_rating_service.create_or_update_rating.return_value = MOCK_RATING

        response = rating_client.post(
            "/courses/curso-de-react/ratings",
            json={
                "score": 5,
                "user_identifier": "550e8400-e29b-41d4-a716-446655440001",
                "comment": "Excelente curso",
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert data["id"] == 1
        assert data["score"] == 5
        assert data["user_identifier"] == "550e8400-e29b-41d4-a716-446655440001"
        assert data["comment"] == "Excelente curso"

        mock_rating_service.create_or_update_rating.assert_called_once_with(
            slug="curso-de-react",
            score=5,
            user_identifier="550e8400-e29b-41d4-a716-446655440001",
            comment="Excelente curso",
        )

    def test_create_rating_course_not_found(self, rating_client, mock_rating_service):
        """Test POST /courses/{slug}/ratings when course doesn't exist"""
        mock_rating_service.create_or_update_rating.return_value = None

        response = rating_client.post(
            "/courses/nonexistent/ratings",
            json={
                "score": 5,
                "user_identifier": "550e8400-e29b-41d4-a716-446655440001",
            },
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Course not found"}

    def test_create_rating_invalid_score_too_low(self, rating_client):
        """Test POST /courses/{slug}/ratings with score < 1"""
        response = rating_client.post(
            "/courses/curso-de-react/ratings",
            json={
                "score": 0,
                "user_identifier": "550e8400-e29b-41d4-a716-446655440001",
            },
        )
        assert response.status_code == 422

    def test_create_rating_invalid_score_too_high(self, rating_client):
        """Test POST /courses/{slug}/ratings with score > 5"""
        response = rating_client.post(
            "/courses/curso-de-react/ratings",
            json={
                "score": 6,
                "user_identifier": "550e8400-e29b-41d4-a716-446655440001",
            },
        )
        assert response.status_code == 422

    def test_create_rating_without_comment(self, rating_client, mock_rating_service):
        """Test POST /courses/{slug}/ratings without optional comment"""
        mock_no_comment = {**MOCK_RATING, "comment": None}
        mock_rating_service.create_or_update_rating.return_value = mock_no_comment

        response = rating_client.post(
            "/courses/curso-de-react/ratings",
            json={
                "score": 4,
                "user_identifier": "550e8400-e29b-41d4-a716-446655440001",
            },
        )
        assert response.status_code == 201
        assert response.json()["comment"] is None

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
        """Test GET /courses/{slug}/ratings when course doesn't exist"""
        mock_rating_service.get_ratings_by_course.return_value = None

        response = rating_client.get("/courses/nonexistent/ratings")
        assert response.status_code == 404

    def test_get_rating_stats_success(self, rating_client, mock_rating_service):
        """Test GET /courses/{slug}/ratings/stats returns statistics"""
        mock_rating_service.get_rating_stats.return_value = MOCK_RATING_STATS

        response = rating_client.get("/courses/curso-de-react/ratings/stats")
        assert response.status_code == 200

        data = response.json()
        assert "average_rating" in data
        assert "ratings_count" in data
        assert isinstance(data["average_rating"], float)
        assert isinstance(data["ratings_count"], int)
        assert data["average_rating"] == 4.5
        assert data["ratings_count"] == 2

        mock_rating_service.get_rating_stats.assert_called_once_with("curso-de-react")

    def test_get_rating_stats_not_found(self, rating_client, mock_rating_service):
        """Test GET /courses/{slug}/ratings/stats when course doesn't exist"""
        mock_rating_service.get_rating_stats.return_value = None

        response = rating_client.get("/courses/nonexistent/ratings/stats")
        assert response.status_code == 404

    def test_delete_rating_success(self, rating_client, mock_rating_service):
        """Test DELETE /ratings/{id} with correct user_identifier"""
        mock_rating_service.delete_rating.return_value = {"message": "Rating deleted successfully"}

        response = rating_client.delete(
            "/ratings/1?user_identifier=550e8400-e29b-41d4-a716-446655440001"
        )
        assert response.status_code == 200
        assert response.json() == {"message": "Rating deleted successfully"}

        mock_rating_service.delete_rating.assert_called_once_with(
            1, "550e8400-e29b-41d4-a716-446655440001"
        )

    def test_delete_rating_not_found(self, rating_client, mock_rating_service):
        """Test DELETE /ratings/{id} when rating doesn't exist or wrong user"""
        mock_rating_service.delete_rating.return_value = None

        response = rating_client.delete(
            "/ratings/999?user_identifier=550e8400-e29b-41d4-a716-446655440001"
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Rating not found or not authorized"}


class TestCoursesWithRatings:
    """Tests to verify existing course endpoints include rating data"""

    def test_courses_list_includes_rating_fields(self, client, mock_course_service):
        """Test GET /courses response includes average_rating and ratings_count"""
        mock_courses_with_ratings = [
            {
                **course,
                "average_rating": 4.5,
                "ratings_count": 10,
            }
            for course in MOCK_COURSES_LIST
        ]
        mock_course_service.get_all_courses.return_value = mock_courses_with_ratings

        response = client.get("/courses")
        data = response.json()

        for course in data:
            assert "average_rating" in course
            assert "ratings_count" in course
            assert isinstance(course["average_rating"], float)
            assert isinstance(course["ratings_count"], int)

    def test_course_detail_includes_rating_fields(self, client, mock_course_service):
        """Test GET /courses/{slug} response includes average_rating and ratings_count"""
        mock_detail_with_ratings = {
            **MOCK_COURSE_DETAIL,
            "average_rating": 4.5,
            "ratings_count": 2,
        }
        mock_course_service.get_course_by_slug.return_value = mock_detail_with_ratings

        response = client.get("/courses/curso-de-react")
        data = response.json()

        assert "average_rating" in data
        assert "ratings_count" in data
        assert data["average_rating"] == 4.5
        assert data["ratings_count"] == 2
```

**Nota:** Los tests existentes de `TestContractCompliance` que verifican que las respuestas contienen SOLO los campos esperados (`expected_fields`) fallaran despues de agregar `average_rating` y `ratings_count`. Hay que actualizarlos:

En `test_courses_list_contract_fields_only`, cambiar:
```python
expected_fields = {"id", "name", "description", "thumbnail", "slug", "average_rating", "ratings_count"}
```

En `test_course_detail_contract_fields_only`, cambiar:
```python
expected_course_fields = {"id", "name", "description", "thumbnail", "slug", "teacher_id", "classes", "average_rating", "ratings_count"}
```

Y actualizar `MOCK_COURSES_LIST` y `MOCK_COURSE_DETAIL` para incluir los nuevos campos:

```python
MOCK_COURSES_LIST = [
    {
        "id": 1,
        "name": "Curso de React",
        "description": "Aprende React desde cero",
        "thumbnail": "https://via.placeholder.com/150",
        "slug": "curso-de-react",
        "average_rating": 4.5,
        "ratings_count": 2,
    },
    {
        "id": 2,
        "name": "Curso de Python",
        "description": "Domina Python paso a paso",
        "thumbnail": "https://via.placeholder.com/200",
        "slug": "curso-de-python",
        "average_rating": 4.0,
        "ratings_count": 5,
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
    "ratings_count": 2,
}
```

---

### Criterio de verificacion de Fase 4

1. Todos los tests existentes pasan (con los mock data actualizados)
2. Los nuevos tests de ratings pasan (12+ tests nuevos)
3. Ejecutar: `docker-compose exec api bash -c "cd /app && uv run pytest app/test_main.py -v"`
4. Total de tests esperado: 13 existentes + 12 nuevos = 25+ tests

---

## Fase 5: Frontend - Tipos, Componentes y Paginas

**Objetivo:** Integrar el sistema de ratings en el frontend con componentes de solo lectura (estrellas) y un formulario interactivo para enviar ratings.

**Dependencias:** Fase 3 completada (API de ratings funcional).

---

### Tarea 5.1: Actualizar tipos TypeScript

**Archivo a modificar:** `Frontend/src/types/index.ts`

**Cambio:** Agregar tipos para ratings y actualizar `Course`/`CourseDetail` para incluir rating stats. Se mantienen los tipos existentes tal cual estan actualmente (con `title`, `teacher`, etc.) ya que el analisis de impacto detecto que estan desalineados con la API, pero ese problema es de la Fase 0 del impact analysis, no de este plan de ratings. Aqui solo agregamos lo necesario para ratings.

```typescript
// Course types
export interface Course {
  id: number;
  title: string;
  teacher: string;
  duration: number;
  thumbnail: string;
  slug: string;
  average_rating: number;   // NUEVO
  ratings_count: number;     // NUEVO
}

// Class types
export interface Class {
  id: number;
  title: string;
  description: string;
  video: string;
  duration: number;
  slug: string;
}

// Course Detail type
export interface CourseDetail extends Course {
  description: string;
  classes: Class[];
}

// Rating types -- NUEVO
export interface Rating {
  id: number;
  course_id: number;
  user_identifier: string;
  score: number;
  comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface RatingCreate {
  score: number;
  user_identifier: string;
  comment?: string;
}

export interface RatingStats {
  average_rating: number;
  ratings_count: number;
}

// Progress types
export interface Progress {
  progress: number; // seconds
  user_id: number;
}

// Quiz types
export interface QuizOption {
  id: number;
  answer: string;
  correct: boolean;
}

export interface Quiz {
  id: number;
  question: string;
  options: QuizOption[];
}

// Favorite types
export interface FavoriteToggle {
  course_id: number;
}
```

---

### Tarea 5.2: Crear utilidad de User ID

**Archivo a crear:** `Frontend/src/utils/userId.ts`

**Descripcion:** Funcion que genera y persiste un UUID v4 en `localStorage`. Se usa como `user_identifier` para las operaciones de rating.

```typescript
/**
 * Gets or creates a persistent user identifier stored in localStorage.
 * Used as user_identifier for anonymous rating operations.
 */
export function getUserId(): string {
  if (typeof window === "undefined") {
    // Server-side: return empty string (ratings require client-side)
    return "";
  }

  const STORAGE_KEY = "platziflix_user_id";
  let userId = localStorage.getItem(STORAGE_KEY);

  if (!userId) {
    userId = crypto.randomUUID();
    localStorage.setItem(STORAGE_KEY, userId);
  }

  return userId;
}
```

**Notas:**
- `crypto.randomUUID()` esta disponible en todos los browsers modernos (Safari 15.4+, Chrome 92+, Firefox 95+).
- La comprobacion `typeof window === "undefined"` previene errores durante Server-Side Rendering.
- El key `platziflix_user_id` es especifico de la aplicacion para evitar colisiones con otros datos en localStorage.

---

### Tarea 5.3: Crear componente `StarRating` (Server Component, solo lectura)

**Archivo a crear:** `Frontend/src/components/StarRating/StarRating.tsx`

**Descripcion:** Componente que muestra estrellas llenas/vacias basandose en un promedio. Es un Server Component (sin `"use client"`) ya que no requiere interactividad -- solo recibe datos y renderiza.

```typescript
import { FC } from "react";
import styles from "./StarRating.module.scss";

interface StarRatingProps {
  average: number;    // 0-5, puede tener decimales
  count: number;      // cantidad total de ratings
  size?: "sm" | "md"; // tamano de estrellas
}

export const StarRating: FC<StarRatingProps> = ({ average, count, size = "md" }) => {
  const fullStars = Math.floor(average);
  const hasHalfStar = average - fullStars >= 0.5;
  const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

  return (
    <div className={`${styles.starRating} ${styles[size]}`}>
      <div className={styles.stars}>
        {Array.from({ length: fullStars }, (_, i) => (
          <span key={`full-${i}`} className={styles.starFull}>&#9733;</span>
        ))}
        {hasHalfStar && (
          <span key="half" className={styles.starHalf}>&#9733;</span>
        )}
        {Array.from({ length: emptyStars }, (_, i) => (
          <span key={`empty-${i}`} className={styles.starEmpty}>&#9734;</span>
        ))}
      </div>
      <span className={styles.info}>
        {average > 0 ? average.toFixed(1) : "Sin ratings"} ({count})
      </span>
    </div>
  );
};
```

**Archivo a crear:** `Frontend/src/components/StarRating/StarRating.module.scss`

```scss
.starRating {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stars {
  display: flex;
  gap: 2px;
}

.starFull {
  color: #fbbf24;
}

.starHalf {
  color: #fbbf24;
  opacity: 0.6;
}

.starEmpty {
  color: color('light-gray');
}

// Size variants
.sm {
  .stars span {
    font-size: 1rem;
  }
  .info {
    font-size: 0.8rem;
  }
}

.md {
  .stars span {
    font-size: 1.4rem;
  }
  .info {
    font-size: 1rem;
  }
}

.info {
  color: color('text-secondary');
  font-weight: 600;
}
```

**Notas de estilo:**
- Usa la funcion `color()` de `vars.scss` (auto-importada via `next.config.ts` con `prependData`).
- El dorado `#fbbf24` es un amarillo estandar para estrellas que no se define en el sistema de colores existente -- se usa directamente para mantener la semantica visual de "rating/estrella".
- Sigue el patron de SCSS Modules con tamanos via clase (`.sm`, `.md`).

---

### Tarea 5.4: Crear componente `RatingForm` (Client Component, interactivo)

**Archivo a crear:** `Frontend/src/components/RatingForm/RatingForm.tsx`

**Descripcion:** Formulario interactivo para que el usuario envie un rating. Es un Client Component (`"use client"`) porque requiere estado local, eventos del usuario y acceso a `localStorage`.

```typescript
"use client";

import { FC, useState } from "react";
import { getUserId } from "@/utils/userId";
import styles from "./RatingForm.module.scss";

interface RatingFormProps {
  courseSlug: string;
  onRatingSubmitted?: () => void;  // callback para refrescar datos
}

export const RatingForm: FC<RatingFormProps> = ({ courseSlug, onRatingSubmitted }) => {
  const [hoveredStar, setHoveredStar] = useState<number>(0);
  const [selectedScore, setSelectedScore] = useState<number>(0);
  const [comment, setComment] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitMessage, setSubmitMessage] = useState<string>("");
  const [submitError, setSubmitError] = useState<boolean>(false);

  const handleSubmit = async () => {
    if (selectedScore === 0) return;

    setIsSubmitting(true);
    setSubmitMessage("");
    setSubmitError(false);

    try {
      const userId = getUserId();
      const response = await fetch(`http://localhost:8000/courses/${courseSlug}/ratings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          score: selectedScore,
          user_identifier: userId,
          comment: comment || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error("Error al enviar el rating");
      }

      setSubmitMessage("Rating enviado correctamente");
      setSubmitError(false);
      setComment("");

      if (onRatingSubmitted) {
        onRatingSubmitted();
      }
    } catch (error) {
      setSubmitMessage("Error al enviar el rating. Intenta de nuevo.");
      setSubmitError(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={styles.ratingForm}>
      <h3 className={styles.title}>Califica este curso</h3>

      <div className={styles.starsInput}>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            className={`${styles.starButton} ${
              star <= (hoveredStar || selectedScore) ? styles.active : ""
            }`}
            onMouseEnter={() => setHoveredStar(star)}
            onMouseLeave={() => setHoveredStar(0)}
            onClick={() => setSelectedScore(star)}
            disabled={isSubmitting}
            aria-label={`${star} estrella${star > 1 ? "s" : ""}`}
          >
            &#9733;
          </button>
        ))}
        {selectedScore > 0 && (
          <span className={styles.scoreLabel}>{selectedScore}/5</span>
        )}
      </div>

      <textarea
        className={styles.commentInput}
        placeholder="Deja un comentario (opcional)"
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        maxLength={1000}
        rows={3}
        disabled={isSubmitting}
      />

      <button
        className={styles.submitButton}
        onClick={handleSubmit}
        disabled={selectedScore === 0 || isSubmitting}
      >
        {isSubmitting ? "Enviando..." : "Enviar rating"}
      </button>

      {submitMessage && (
        <p className={`${styles.message} ${submitError ? styles.error : styles.success}`}>
          {submitMessage}
        </p>
      )}
    </div>
  );
};
```

**Archivo a crear:** `Frontend/src/components/RatingForm/RatingForm.module.scss`

```scss
.ratingForm {
  background: color('off-white');
  border-radius: 18px;
  padding: 2rem;
  border: 2px solid color('light-gray');
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.title {
  font-size: 1.5rem;
  font-weight: 800;
  color: color('text-primary');
}

.starsInput {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.starButton {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 2rem;
  color: color('light-gray');
  transition: color 0.15s, transform 0.15s;
  padding: 0;
  line-height: 1;

  &:hover,
  &.active {
    color: #fbbf24;
    transform: scale(1.15);
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }
}

.scoreLabel {
  margin-left: 0.75rem;
  font-size: 1.1rem;
  font-weight: 700;
  color: color('text-secondary');
}

.commentInput {
  width: 100%;
  padding: 1rem;
  border: 2px solid color('light-gray');
  border-radius: 12px;
  font-family: inherit;
  font-size: 1rem;
  resize: vertical;
  min-height: 80px;
  transition: border-color 0.2s;
  box-sizing: border-box;

  &:focus {
    outline: none;
    border-color: color('primary');
  }

  &:disabled {
    opacity: 0.5;
  }
}

.submitButton {
  background: color('primary');
  color: color('white');
  border: none;
  padding: 0.85rem 2rem;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  align-self: flex-start;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px color('primary-light');
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.message {
  font-size: 1rem;
  font-weight: 600;
  padding: 0.75rem 1rem;
  border-radius: 8px;
}

.success {
  color: #16a34a;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.error {
  color: color('primary');
  background: rgba(255, 45, 45, 0.05);
  border: 1px solid color('primary-border');
}
```

---

### Tarea 5.5: Integrar `StarRating` en el componente `Course` (card de la home)

**Archivo a modificar:** `Frontend/src/components/Course/Course.tsx`

**Cambio:** Agregar `StarRating` al card del curso. El componente ya recibe props via `Omit<CourseType, "slug">`, por lo que `average_rating` y `ratings_count` estan disponibles automaticamente despues de actualizar el tipo.

```typescript
import styles from "./Course.module.scss";
import { Course as CourseType } from "@/types";
import { StarRating } from "@/components/StarRating/StarRating";

type CourseProps = Omit<CourseType, "slug">;

export const Course = ({ id, title, teacher, duration, thumbnail, average_rating, ratings_count }: CourseProps) => {
  return (
    <article className={styles.courseCard}>
      <div className={styles.thumbnailContainer}>
        <img src={thumbnail} alt={title} className={styles.thumbnail} />
      </div>
      <div className={styles.courseInfo}>
        <h2 className={styles.courseTitle}>{title}</h2>
        <p className={styles.teacher}>Profesor: {teacher}</p>
        <StarRating average={average_rating} count={ratings_count} size="sm" />
        <p className={styles.duration}>Duracion: {duration} minutos</p>
      </div>
    </article>
  );
};
```

---

### Tarea 5.6: Integrar `StarRating` y `RatingForm` en la pagina de detalle

**Archivo a modificar:** `Frontend/src/components/CourseDetail/CourseDetail.tsx`

**Cambio:** Agregar `StarRating` en el header del curso (junto a stats) y agregar `RatingForm` al final del contenido. Como `CourseDetailComponent` es un Server Component y `RatingForm` es un Client Component, Next.js permite esta composicion directamente.

```typescript
import { FC } from "react";
import Link from "next/link";
import { CourseDetail } from "@/types";
import { StarRating } from "@/components/StarRating/StarRating";
import { RatingForm } from "@/components/RatingForm/RatingForm";
import styles from "./CourseDetail.module.scss";

interface CourseDetailComponentProps {
  course: CourseDetail;
}

export const CourseDetailComponent: FC<CourseDetailComponentProps> = ({ course }) => {
  const formatDuration = (duration: number) => {
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const totalDuration = course.classes.reduce((acc, cls) => acc + cls.duration, 0);

  return (
    <div className={styles.container}>
      <div className={styles.navigation}>
        <Link href="/" className={styles.backButton}>
          ← Volver a cursos
        </Link>
      </div>
      <div className={styles.header}>
        <div className={styles.thumbnailContainer}>
          <img src={course.thumbnail} alt={course.title} className={styles.thumbnail} />
        </div>
        <div className={styles.courseInfo}>
          <h1 className={styles.title}>{course.title}</h1>
          <p className={styles.teacher}>Por {course.teacher}</p>
          <StarRating average={course.average_rating} count={course.ratings_count} size="md" />
          <p className={styles.description}>{course.description}</p>
          <div className={styles.stats}>
            <span className={styles.duration}>Duracion total: {formatDuration(totalDuration)}</span>
            <span className={styles.classCount}>{course.classes.length} clases</span>
          </div>
        </div>
      </div>

      <div className={styles.classesSection}>
        <h2 className={styles.sectionTitle}>Contenido del curso</h2>
        <div className={styles.classesList}>
          {course.classes.map((cls, index) => (
            <Link href={`/classes/${cls.id}`} key={cls.id} className={styles.classItem}>
              <div className={styles.classNumber}>{(index + 1).toString().padStart(2, "0")}</div>
              <div className={styles.classInfo}>
                <h3 className={styles.classTitle}>{cls.title}</h3>
                <p className={styles.classDescription}>{cls.description}</p>
                <span className={styles.classDuration}>{formatDuration(cls.duration)}</span>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Rating section */}
      <div className={styles.ratingSection}>
        <RatingForm courseSlug={course.slug} />
      </div>
    </div>
  );
};
```

**Archivo a modificar:** `Frontend/src/components/CourseDetail/CourseDetail.module.scss`

**Cambio:** Agregar estilos para la seccion de rating al final del archivo.

```scss
.ratingSection {
  margin-top: 3rem;
}
```

---

### Tarea 5.7: Pasar rating props en la Home page

**Archivo a modificar:** `Frontend/src/app/page.tsx`

**Cambio:** Agregar `average_rating` y `ratings_count` a los props del componente Course.

El componente ya recibe spread props excepto `slug`, por lo que basta con verificar que el map pasa los nuevos campos. Dado que `CourseComponent` usa `Omit<CourseType, "slug">`, los nuevos campos se propagaran si estan en los datos:

```typescript
{courses.map((course) => (
  <Link href={`/course/${course.slug}`} key={course.id}>
    <CourseComponent
      id={course.id}
      title={course.title}
      teacher={course.teacher}
      duration={course.duration}
      thumbnail={course.thumbnail}
      average_rating={course.average_rating}
      ratings_count={course.ratings_count}
    />
  </Link>
))}
```

---

### Tarea 5.8: Actualizar tests del Frontend

**Archivo a modificar:** `Frontend/src/components/Course/__test__/Course.test.tsx`

**Cambio:** Agregar `average_rating` y `ratings_count` al mock data.

```typescript
const mockCourse = {
  id: 1,
  title: "React Fundamentals",
  teacher: "John Doe",
  duration: 120,
  thumbnail: "https://example.com/thumbnail.jpg",
  average_rating: 4.5,
  ratings_count: 10,
};
```

Agregar test para verificar que se renderizan las estrellas:

```typescript
it("renders star rating", () => {
  render(<Course {...mockCourse} />);

  // StarRating shows the average and count
  expect(screen.getByText("4.5 (10)")).toBeDefined();
});
```

---

### Criterio de verificacion de Fase 5

1. `yarn dev` compila sin errores
2. La Home page muestra estrellas de rating en cada course card
3. La pagina de detalle muestra estrellas y el formulario de rating
4. El formulario permite seleccionar estrellas con hover effect
5. Enviar un rating via el formulario funciona contra la API
6. Enviar otro rating con el mismo browser actualiza el anterior (upsert)
7. `yarn test` pasa todos los tests actualizados

---

## Consideraciones Tecnicas

### Performance

1. **Queries N+1:** La implementacion actual de `_get_rating_stats` en `CourseService` ejecuta una query de agregacion por curso en `get_all_courses()`. Con 3 cursos es irrelevante, pero con 100+ cursos se deberia optimizar con una sola query:
   ```python
   # Optimizacion futura: subquery con groupby
   stats_subquery = (
       self.db.query(
           Rating.course_id,
           func.avg(Rating.score).label("avg"),
           func.count(Rating.id).label("cnt"),
       )
       .filter(Rating.deleted_at.is_(None))
       .group_by(Rating.course_id)
       .subquery()
   )
   ```

2. **Indices:** La tabla `ratings` tiene indices en `course_id` y `user_identifier`. El indice compuesto de la constraint `UNIQUE(course_id, user_identifier)` tambien cubre queries por `course_id` eficientemente.

3. **`cache: "no-store"` en Next.js:** Cada pageview fetcha datos frescos del backend. Esto asegura que los ratings siempre estan actualizados, pero si el trafico crece, se deberia considerar `revalidate` con un TTL corto (ej: 60 segundos).

### Seguridad

1. **Sin autenticacion:** Cualquier usuario puede enviar ratings con cualquier `user_identifier`. No hay forma de prevenir que un usuario malicioso envie multiples ratings cambiando el UUID. Mitigaciones posibles:
   - Rate limiting por IP (fuera del scope de este plan)
   - Validacion de formato UUID (implementada en el schema Pydantic con `min_length=36`)

2. **Inyeccion SQL:** No aplica -- SQLAlchemy usa parametros preparados en todas las queries.

3. **XSS en comentarios:** Los comentarios se almacenan como texto plano y React/Next.js escapan automaticamente el contenido renderizado. No hay riesgo de XSS a menos que se use `dangerouslySetInnerHTML`.

4. **Ownership del delete:** Solo el `user_identifier` que creo el rating puede eliminarlo. Sin embargo, el UUID es visible en el `localStorage` del browser y podria ser copiado. Esto es una limitacion aceptable sin autenticacion real.

### Edge Cases

1. **Curso sin ratings:** `average_rating` sera `0.0` y `ratings_count` sera `0`. El componente `StarRating` muestra "Sin ratings (0)".

2. **Comentario nulo vs vacio:** El schema Pydantic acepta `None` (campo omitido en JSON) y `""`. El modelo acepta `nullable=True`. Para consistencia, el frontend envia `undefined` (omitido) cuando el textarea esta vacio, no `""`.

3. **Rating duplicado (upsert):** El endpoint `POST /courses/{slug}/ratings` detecta si ya existe un rating con el mismo `(course_id, user_identifier)` y lo actualiza en lugar de crear uno nuevo. No se usa `INSERT ... ON CONFLICT` de PostgreSQL directamente -- se hace a nivel de aplicacion para mayor claridad y compatibilidad.

4. **Curso eliminado (soft delete):** Todas las queries de ratings filtran `Course.deleted_at.is_(None)`, por lo que un curso "eliminado" no aceptara ratings nuevos ni mostrara los existentes.

5. **Rating eliminado (soft delete):** Los ratings eliminados (`deleted_at IS NOT NULL`) se excluyen de las consultas de listado y estadisticas automticamente.

---

## Riesgos y Mitigaciones

| # | Riesgo | Probabilidad | Impacto | Mitigacion |
|---|--------|-------------|---------|------------|
| 1 | Spam de ratings sin auth | Alta | Medio | Validar formato UUID. Plan futuro: rate limiting por IP |
| 2 | N+1 queries en listado de cursos | Baja (3 cursos) | Bajo | Documentado como optimizacion futura con subquery |
| 3 | Migracion Alembic falla en ambiente existente | Baja | Alto | Verificar con `make migrate` en desarrollo antes de deploy. El `down_revision` apunta a la migracion inicial correcta |
| 4 | Frontend tests fallan por campos nuevos en mocks | Alta | Bajo | Actualizar mock data y expected fields en Fase 4 antes de Fase 5 |
| 5 | Colision de UUID en localStorage | Casi nula | Bajo | UUID v4 tiene 2^122 combinaciones posibles. No es un riesgo practico |
| 6 | Desalineacion de tipos Frontend-API preexistente | Ya existente | Alto | Este plan agrega campos de rating sobre los tipos existentes. La desalineacion de `title`/`name`, `teacher`/`teacher_id`, etc. es un problema preexistente documentado en el analisis de impacto (Fase 0) y debe resolverse por separado |
| 7 | Browser sin soporte para `crypto.randomUUID()` | Baja | Medio | Browsers modernos (2022+) todos lo soportan. Alternativa: usar libreria `uuid` |

---

## Resumen de Archivos

### Archivos Nuevos (8)

| # | Ruta | Descripcion |
|---|------|-------------|
| 1 | `Backend/app/models/rating.py` | Modelo SQLAlchemy Rating |
| 2 | `Backend/app/schemas/__init__.py` | Modulo de schemas Pydantic |
| 3 | `Backend/app/schemas/rating.py` | Schemas RatingCreate, RatingResponse, RatingStats |
| 4 | `Backend/app/services/rating_service.py` | Servicio con logica de negocio de ratings |
| 5 | `Frontend/src/utils/userId.ts` | Generador de UUID persistente en localStorage |
| 6 | `Frontend/src/components/StarRating/StarRating.tsx` | Componente de estrellas (solo lectura) |
| 7 | `Frontend/src/components/StarRating/StarRating.module.scss` | Estilos de StarRating |
| 8 | `Frontend/src/components/RatingForm/RatingForm.tsx` | Formulario interactivo de rating |
| 9 | `Frontend/src/components/RatingForm/RatingForm.module.scss` | Estilos de RatingForm |

### Archivos Modificados (13)

| # | Ruta | Descripcion del cambio |
|---|------|----------------------|
| 1 | `Backend/app/models/__init__.py` | Agregar import de Rating |
| 2 | `Backend/app/models/course.py` | Agregar relacion `ratings` |
| 3 | `Backend/app/services/__init__.py` | Agregar export de RatingService |
| 4 | `Backend/app/services/course_service.py` | Agregar `_get_rating_stats`, modificar respuestas |
| 5 | `Backend/app/main.py` | Agregar 4 endpoints + dependency de RatingService |
| 6 | `Backend/app/db/seed.py` | Agregar ratings de ejemplo + limpiar ratings en clear |
| 7 | `Backend/app/test_main.py` | Agregar 12+ tests, actualizar mocks existentes |
| 8 | `Backend/specs/00_contracts.md` | Agregar entidad Rating, endpoints, actualizar contratos existentes |
| 9 | `Frontend/src/types/index.ts` | Agregar Rating, RatingCreate, RatingStats; actualizar Course |
| 10 | `Frontend/src/components/Course/Course.tsx` | Agregar StarRating al card |
| 11 | `Frontend/src/components/CourseDetail/CourseDetail.tsx` | Agregar StarRating + RatingForm |
| 12 | `Frontend/src/components/CourseDetail/CourseDetail.module.scss` | Agregar `.ratingSection` |
| 13 | `Frontend/src/app/page.tsx` | Pasar average_rating y ratings_count a CourseComponent |

**Nota:** Se genera 1 archivo adicional automaticamente: la migracion Alembic (via `make create-migration`). Total real: 10 archivos nuevos, 13 modificados.
