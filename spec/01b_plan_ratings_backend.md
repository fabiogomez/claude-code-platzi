# Backend Implementation Plan: Ratings System

**Date:** 2026-04-06
**Base branch:** `start-zero`
**Author:** Backend Specialist (Claude Opus 4.6)
**Previous document:** `spec/01_plan_ratings.md` (architect's plan)

---

## Summary

This document translates the architect's plan into specific implementation phases for the backend, based on a direct reading of the current codebase. Each phase is ordered by strict dependency: a phase cannot be started without having completed and verified the previous one.

Discrepancies found between what the architect proposed and what actually exists in the code are included.

---

## Detected Discrepancies Between the Architect's Plan and the Actual Code

### D1: Orphan `Class` model (file `class.py`)

`Backend/app/models/class.py` exists with a `Class` model (tablename `classes`) that has `back_populates="classes"` pointing to `Course`. However:
- **It is not imported** in `Backend/app/models/__init__.py` (it is not in `__all__`).
- **Course does not have a `classes` relationship** -- it only has `lessons` and `teachers`.
- The `Lesson` model (tablename `lessons`) is the one actually used in production.

**Impact on ratings:** No direct impact, but it is important to know because the endpoints return a key `"classes"` in the response for `GET /courses/{slug}`, which actually maps data from the `lessons` table. This is not a ratings bug but a pre-existing inconsistency. We do not touch it in this plan.

### D2: The architect's plan mentions `Backend/app/schemas/rating.py` as a new file

The `Backend/app/schemas/` directory does not currently exist. No existing endpoint uses Pydantic response models -- the endpoints return `dict` and `list` directly. Creating schemas is correct for validating the POST input (the first endpoint that receives user data), but it is a new pattern in the project. This should be documented as an explicit design decision in the corresponding phase.

### D3: `CourseService` uses `Lesson` but the response says `"classes"`

In `Backend/app/services/course_service.py`, line 68, the `get_course_by_slug` method iterates over `course.lessons` but uses the key `"classes"` in the response dict. This is intentional to maintain compatibility with the API contract (`00_contracts.md` uses `classes`). When adding rating stats to this response, we must preserve this naming.

### D4: Duplication of `_get_rating_stats` and `get_rating_stats_for_course_id` logic

The architect's plan proposes:
- A private method `_get_rating_stats(course_id)` inside `CourseService`.
- A public method `get_rating_stats_for_course_id(course_id)` inside `RatingService`.

Both do exactly the same thing (AVG/COUNT on ratings filtered by `course_id` and `deleted_at`). This is duplication. The recommendation is:
- **Option A (minimal friction):** Keep `_get_rating_stats` in `CourseService` as the architect proposes, accepting the duplication for simplicity and low coupling between services.
- **Option B (DRY):** Have `CourseService` use `RatingService` internally to get the stats, but this introduces a circular import dependency or requires injection of both services.

**Recommended decision:** Option A. With 3 courses, the duplication is trivial, and it avoids complicating the dependency injection. If stats are pre-calculated in the future, it can be removed from both places.

### D5: The `POST` always returns status 201

The architect proposes `status_code=201` for the `POST /courses/{slug}/ratings` endpoint. However, this endpoint performs an upsert (create or update). Semantically, it should return `201 Created` for new creations and `200 OK` for updates. Since the service does not distinguish between create and update in the return value, the current implementation simplifies by always returning 201. This is acceptable for the MVP but is noted as minor technical debt.

### D6: Route declaration order in FastAPI

The architect warns that `/courses/{slug}/ratings/stats` must be declared AFTER `/courses/{slug}/ratings`. In reality, in FastAPI the order matters when there is path parameter ambiguity. Since `stats` is a literal subroute under `ratings`, there is no conflict with `ratings` which has no subroute -- but if `/courses/{slug}/ratings/{rating_id}` (which does not exist in the plan) were declared first, then there would be a conflict. The architect's note is correct as a preventive measure.

---

## Phase 1: Data Model and Migration [COMPLETED]

**Objective:** Create the `ratings` table in the database with the corresponding SQLAlchemy model, including constraints, indexes, and sample data.

**Dependencies:** None. This phase is the foundation for everything else.

**Status:** Completed on 2026-04-14. All verification criteria passed: table exists with correct columns/constraints/indexes, seed-fresh creates 5 ratings, score range and uniqueness constraints enforced, 10/10 existing tests still passing.

### Task 1.1: Create the `Rating` model file

**File:** `Backend/app/models/rating.py` (NEW)

**What to do:**
- Create a new `Rating` model that inherits from `BaseModel` (inherits `id`, `created_at`, `updated_at`, `deleted_at` automatically).
- Define columns: `course_id` (FK to `courses.id`, non-nullable, with index), `user_identifier` (String 255, non-nullable, with index), `score` (Integer, non-nullable), `comment` (Text, nullable).
- Add a `UniqueConstraint` on `(course_id, user_identifier)` named `uq_rating_course_user`.
- Add a `CheckConstraint` for `score >= 1 AND score <= 5` named `ck_rating_score_range`.
- Define `relationship("Course", back_populates="ratings")`.
- Include `__repr__` following the pattern of existing models: `f"<Rating(id={self.id}, course_id={self.course_id}, score={self.score})>"`.

**Conventions to follow (extracted from the actual code):**
- Same import structure as `lesson.py`: `from sqlalchemy import Column, String, Text, Integer, ForeignKey` + add `UniqueConstraint, CheckConstraint`.
- `from sqlalchemy.orm import relationship`.
- `from .base import BaseModel`.
- `__tablename__ = 'ratings'` (plural, like `courses`, `lessons`, `teachers`).
- FK pattern: `Column(Integer, ForeignKey('courses.id'), nullable=False, index=True)` -- identical to `Lesson.course_id`.

### Task 1.2: Register `Rating` in the models package

**File:** `Backend/app/models/__init__.py` (MODIFY)

**What to do:**
- Add `from .rating import Rating` to the imports.
- Add `'Rating'` to the `__all__` list.

**Why:** Alembic detects models via `from app.models import *` in `env.py` (line 27). If `Rating` is not in `__init__.py`, the autogenerated migration will not create the table.

### Task 1.3: Add inverse `ratings` relationship to `Course`

**File:** `Backend/app/models/course.py` (MODIFY)

**What to do:**
- Add a new `ratings` relationship after the existing `lessons` relationship.
- Use the same pattern as `lessons`: `relationship("Rating", back_populates="course", cascade="all, delete-orphan")`.

**Why:** Without the inverse relationship, SQLAlchemy throws an error when trying to use `back_populates="ratings"` in the `Rating` model.

### Task 1.4: Generate and review the Alembic migration

**Command:**
```bash
make create-migration
# Message: "Add ratings table with score user_identifier and course relationship"
```

**What to do after generating:**
- Review the generated file in `Backend/app/alembic/versions/` to confirm it contains:
  - `op.create_table('ratings', ...)` with all columns.
  - The `uq_rating_course_user` and `ck_rating_score_range` constraints.
  - Indexes on `id`, `course_id`, and `user_identifier`.
- Verify that the `downgrade()` does `op.drop_table('ratings')` correctly.
- Apply the migration: `make migrate`.

### Task 1.5: Add ratings to the data seed

**File:** `Backend/app/db/seed.py` (MODIFY)

**What to do in `create_sample_data()`:**
- Add `Rating` to the existing import from `app.models`.
- After the lessons commit and before the final print, create 5 sample ratings distributed across the 3 courses with different `user_identifier` values (fixed UUIDs), varied scores (3, 4, 5), and some with `comment` set to `None`.
- Add a `db.commit()` after inserting the ratings.
- Update the final print to include the rating count.

**What to do in `clear_all_data()`:**
- Add `from app.models import Rating` if not already imported (it is in the global import).
- Add `db.query(Rating).delete()` BEFORE `db.query(Lesson).delete()` and BEFORE `db.query(Course).delete()` -- because of the FK from `ratings.course_id` to `courses.id`.

**Why order matters:** If you try to delete courses before ratings, PostgreSQL throws a FK constraint violation error.

### Phase 1 Verification Criteria

1. `make migrate` runs without errors.
2. Verify in PostgreSQL that the `ratings` table exists with the correct columns, constraints, and indexes:
   ```bash
   docker-compose exec db psql -U platziflix_user -d platziflix_db -c "\d ratings"
   ```
3. `make seed-fresh` runs without errors and creates 5 sample ratings.
4. Verify with direct SQL:
   ```bash
   docker-compose exec db psql -U platziflix_user -d platziflix_db -c "SELECT COUNT(*) FROM ratings"
   ```
   It should return 5.
5. Verify uniqueness constraint: attempting to insert a duplicate rating (same `course_id` + `user_identifier`) should fail.
6. Verify score constraint: attempting to insert a rating with `score = 0` or `score = 6` should fail.

---

## Phase 2: Pydantic Schemas and Rating Service [COMPLETED]

**Objective:** Create input validation with Pydantic schemas and all the business logic for ratings CRUD, including the modification of `CourseService` to enrich responses with stats.

**Status:** Completed on 2026-04-14. Schemas created (RatingCreate, RatingResponse, RatingStats), RatingService implemented with all CRUD methods, CourseService enriched with rating stats in both endpoints.

**Dependencies:** Phase 1 completed (the `Rating` model exists, migration applied, seed functional).

### Task 2.1: Create the Pydantic schemas module

**File:** `Backend/app/schemas/__init__.py` (NEW)

**What to do:**
- Create the `Backend/app/schemas/` directory.
- Create `__init__.py` that imports and exports `RatingCreate`, `RatingResponse`, `RatingStats`.

**File:** `Backend/app/schemas/rating.py` (NEW)

**What to do:**
- `RatingCreate(BaseModel)`: fields `score` (int, ge=1, le=5), `user_identifier` (str, min_length=36, max_length=255), `comment` (Optional[str], max_length=1000). Use `pydantic.Field` for validations.
- `RatingResponse(BaseModel)`: fields `id`, `course_id`, `user_identifier`, `score`, `comment` (Optional), `created_at` (datetime), `updated_at` (datetime).
- `RatingStats(BaseModel)`: fields `average_rating` (float), `ratings_count` (int).

**Design decision note:** This is the first use of Pydantic response schemas in the project. Existing endpoints return `dict`/`list` without schemas. Schemas are introduced here because the ratings POST is the first endpoint that receives user data and needs robust validation. The response schemas (`RatingResponse`, `RatingStats`) are created for reference and documentation but are not used as `response_model` in the endpoints (to maintain consistency with the existing pattern of returning dicts).

### Task 2.2: Create `RatingService`

**File:** `Backend/app/services/rating_service.py` (NEW)

**What to do:**
- Class `RatingService` with `def __init__(self, db: Session)` -- identical to the `CourseService` pattern.
- Method `create_or_update_rating(slug, score, user_identifier, comment=None) -> Optional[Dict]`:
  - Look up course by slug (filtering `deleted_at.is_(None)`).
  - If it does not exist, return `None`.
  - Look up existing rating by `(course_id, user_identifier, deleted_at is None)`.
  - If it exists: update `score` and `comment`, commit and refresh.
  - If it does not exist: create new `Rating`, add, commit, refresh.
  - Return a dict with the rating fields (with `created_at`/`updated_at` as `.isoformat()`).
- Method `get_ratings_by_course(slug) -> Optional[List[Dict]]`:
  - Look up course by slug. If it does not exist, return `None`.
  - Query the course's ratings (filter `deleted_at`), order by `created_at` desc.
  - Return a list of dicts.
- Method `get_rating_stats(slug) -> Optional[Dict]`:
  - Look up course by slug. If it does not exist, return `None`.
  - Query with `func.avg(Rating.score)` and `func.count(Rating.id)`, filtered by `course_id` and `deleted_at`.
  - Use `func.coalesce(..., 0)` for avg when there are no ratings.
  - Return a dict with `average_rating` (rounded to 1 decimal) and `ratings_count`.
- Method `delete_rating(rating_id, user_identifier) -> Optional[Dict]`:
  - Look up rating by `id`, `user_identifier`, and `deleted_at is None`.
  - If it does not exist (or user_identifier does not match), return `None`.
  - Perform soft delete: assign `datetime.utcnow()` to `deleted_at`, commit.
  - Return `{"message": "Rating deleted successfully"}`.
- Method `get_rating_stats_for_course_id(course_id) -> Dict` (internal use):
  - Same stats logic but receives `course_id` directly instead of `slug`.
  - Used by `CourseService` to enrich listings (see discrepancy D4 above).

**Conventions to follow:**
- Imports identical in style to `course_service.py`: `from typing import List, Optional, Dict, Any`.
- Add `from sqlalchemy import func` for aggregation functions.
- Return dicts, not Pydantic objects (consistent with `CourseService`).
- Docstrings in English, same format as `CourseService`.

### Task 2.3: Register `RatingService` in the services package

**File:** `Backend/app/services/__init__.py` (MODIFY)

**What to do:**
- Add `from .rating_service import RatingService`.
- Add `'RatingService'` to `__all__`.

### Task 2.4: Modify `CourseService` to include rating stats

**File:** `Backend/app/services/course_service.py` (MODIFY)

**What to do:**
- Add imports: `from sqlalchemy import func` and `from app.models.rating import Rating`.
- Create private method `_get_rating_stats(self, course_id: int) -> Dict[str, Any]`:
  - Query with `func.coalesce(func.avg(Rating.score), 0)` and `func.count(Rating.id)`.
  - Filter by `Rating.course_id == course_id` and `Rating.deleted_at.is_(None)`.
  - Return `{"average_rating": round(float(...), 1), "ratings_count": ...}`.
- Modify `get_all_courses()`:
  - In each course's dict, add `**self._get_rating_stats(course.id)` to include `average_rating` and `ratings_count`.
- Modify `get_course_by_slug()`:
  - In the return dict, add `**self._get_rating_stats(course.id)` to include `average_rating` and `ratings_count`.
  - Keep the `"classes"` key intact (see discrepancy D3).

**Critical impact:** This modification CHANGES the response contract of the existing `GET /courses` and `GET /courses/{slug}` endpoints. The existing `TestContractCompliance` tests will fail until they are updated in Phase 4. This is expected and acceptable because Phase 4 (tests) runs immediately after.

### Phase 2 Verification Criteria

1. `from app.services.rating_service import RatingService` works without errors.
2. `from app.schemas.rating import RatingCreate, RatingResponse, RatingStats` works without errors.
3. With the server running and seed data loaded:
   - `GET /courses` returns each course with `average_rating` and `ratings_count` as additional fields.
   - `GET /courses/curso-de-react` includes `average_rating` and `ratings_count`.
4. The rating stats values are consistent with the seed data (e.g., if React has 2 ratings with scores 5 and 4, the average should be 4.5).

---

## Phase 3: API Endpoints [COMPLETED]

**Objective:** Expose the 4 new ratings endpoints in `main.py` using the existing dependency injection pattern.

**Status:** Completed on 2026-04-14. Four endpoints added (POST, GET list, GET stats, DELETE). API contracts updated with Rating entity and all new endpoints.

**Dependencies:** Phase 2 completed.

### Task 3.1: Add dependency factory and ratings endpoints

**File:** `Backend/app/main.py` (MODIFY)

**What to do -- new imports:**
- Add `from app.services.rating_service import RatingService`.
- Add `from app.schemas.rating import RatingCreate`.

**What to do -- new dependency factory:**
- Create `get_rating_service(db: Session = Depends(get_db)) -> RatingService` with the exact same pattern as `get_course_service`.

**What to do -- 4 new endpoints (after the courses endpoints):**

1. `POST /courses/{slug}/ratings` (status_code=201):
   - Receives `slug` (path), `rating_data: RatingCreate` (body), `rating_service` (DI).
   - Calls `rating_service.create_or_update_rating(slug, rating_data.score, rating_data.user_identifier, rating_data.comment)`.
   - If it returns `None`, raises `HTTPException(404, "Course not found")`.
   - If ok, returns the rating dict.

2. `GET /courses/{slug}/ratings`:
   - Receives `slug` (path), `rating_service` (DI).
   - Calls `rating_service.get_ratings_by_course(slug)`.
   - If it returns `None`, raises 404.
   - If ok, returns the list.

3. `GET /courses/{slug}/ratings/stats`:
   - Receives `slug` (path), `rating_service` (DI).
   - Calls `rating_service.get_rating_stats(slug)`.
   - If it returns `None`, raises 404.
   - If ok, returns the stats dict.

4. `DELETE /ratings/{rating_id}`:
   - Receives `rating_id` (path), `user_identifier` (query param), `rating_service` (DI).
   - Calls `rating_service.delete_rating(rating_id, user_identifier)`.
   - If it returns `None`, raises `HTTPException(404, "Rating not found or not authorized")`.
   - If ok, returns the message dict.

**Important declaration order:**
- The 4 ratings endpoints must go AFTER the existing courses endpoints.
- Within ratings, the order should be: POST, GET list, GET stats, DELETE.
- The stats endpoint `/courses/{slug}/ratings/stats` must be declared so that FastAPI does not confuse `stats` with a path parameter.

### Task 3.2: Update API contracts

**File:** `Backend/specs/00_contracts.md` (MODIFY)

**What to do:**
- Add the `Rating` entity in the entities section, with its example JSON schema.
- Add the 4 new ratings endpoints with their example request/response bodies.
- Update the existing contracts for `GET /courses` and `GET /courses/:slug` to include the `average_rating` and `ratings_count` fields in the example JSON.

### Phase 3 Verification Criteria

1. The app starts without errors: `make start` and check logs.
2. Verify in `/docs` (Swagger UI) that the 4 new endpoints appear.
3. Manual testing with curl or from Swagger:
   - `POST /courses/curso-de-react/ratings` with a valid body returns 201.
   - `POST /courses/curso-de-react/ratings` with the same `user_identifier` updates (returns 201 with updated data).
   - `POST /courses/nonexistent/ratings` returns 404.
   - `POST` with `score: 0` returns 422 (Pydantic validation).
   - `POST` with `score: 6` returns 422.
   - `GET /courses/curso-de-react/ratings` returns the list of ratings.
   - `GET /courses/curso-de-react/ratings/stats` returns stats.
   - `DELETE /ratings/{id}?user_identifier=<uuid>` with the correct UUID returns 200.
   - `DELETE /ratings/{id}?user_identifier=wrong` returns 404.
4. `GET /courses` returns courses with `average_rating` and `ratings_count`.
5. `GET /courses/curso-de-react` includes `average_rating` and `ratings_count`.

---

## Phase 4: Backend Tests [COMPLETED]

**Objective:** Update existing tests to reflect the new contract and add 12+ new tests for the ratings endpoints.

**Status:** Completed on 2026-04-14. 23 total tests (10 original updated + 13 new), all passing. Mock data updated, contract tests updated, 11 rating endpoint tests + 2 courses-with-ratings tests added.

**Dependencies:** Phase 3 completed. The existing contract tests will be failing at this point because the responses now include `average_rating` and `ratings_count`.

### Task 4.1: Update global mock data

**File:** `Backend/app/test_main.py` (MODIFY)

**What to do:**
- Add to `MOCK_COURSES_LIST`: each course must include `"average_rating"` and `"ratings_count"`.
- Add to `MOCK_COURSE_DETAIL`: include `"average_rating"` and `"ratings_count"`.
- Create new constants: `MOCK_RATING`, `MOCK_RATINGS_LIST`, `MOCK_RATING_STATS`.

### Task 4.2: Add new imports and fixtures

**File:** `Backend/app/test_main.py` (MODIFY)

**What to do:**
- Add import for `RatingService` and `get_rating_service`.
- Create fixture `mock_rating_service` with `Mock(spec=RatingService)`.
- Create fixture `rating_client` that overrides both `get_course_service` and `get_rating_service` and cleans up with `app.dependency_overrides.clear()`.

### Task 4.3: Update existing contract tests

**File:** `Backend/app/test_main.py` (MODIFY)

**What to do in `TestContractCompliance`:**
- In `test_courses_list_contract_fields_only`: update `expected_fields` to include `"average_rating"` and `"ratings_count"`.
- In `test_course_detail_contract_fields_only`: update `expected_course_fields` to include `"average_rating"` and `"ratings_count"`.
- In `test_courses_response_data_matches_contract_examples`: update the mock to include the new fields.

### Task 4.4: Add tests for ratings endpoints

**File:** `Backend/app/test_main.py` (MODIFY)

**What to do -- new class `TestRatingEndpoints`:**

Tests to implement (all follow the AAA pattern: Arrange mock, Act request, Assert response):

1. `test_create_rating_success` -- POST with a valid body, verify 201 and response structure.
2. `test_create_rating_course_not_found` -- POST with a nonexistent slug, verify 404.
3. `test_create_rating_invalid_score_too_low` -- POST with score=0, verify 422.
4. `test_create_rating_invalid_score_too_high` -- POST with score=6, verify 422.
5. `test_create_rating_without_comment` -- POST without comment, verify 201 and comment=null.
6. `test_get_course_ratings_success` -- GET list, verify 200, structure of each rating.
7. `test_get_course_ratings_not_found` -- GET list with nonexistent slug, verify 404.
8. `test_get_rating_stats_success` -- GET stats, verify 200 and fields `average_rating`, `ratings_count`.
9. `test_get_rating_stats_not_found` -- GET stats with nonexistent slug, verify 404.
10. `test_delete_rating_success` -- DELETE with correct user_identifier, verify 200 and message.
11. `test_delete_rating_not_found` -- DELETE with nonexistent rating or incorrect user_identifier, verify 404.

**What to do -- new class `TestCoursesWithRatings`:**

12. `test_courses_list_includes_rating_fields` -- GET /courses includes `average_rating` and `ratings_count` in each course.
13. `test_course_detail_includes_rating_fields` -- GET /courses/{slug} includes `average_rating` and `ratings_count`.

**Pattern for each test (extracted from the existing code):**
```
1. Configure mock: mock_service.method.return_value = MOCK_DATA
2. Make request with client/rating_client
3. Verify status_code
4. Verify response structure (fields present, correct types)
5. Verify that the mock was called with the correct arguments
```

### Phase 4 Verification Criteria

1. Run:
   ```bash
   docker-compose exec api bash -c "cd /app && uv run pytest app/test_main.py -v"
   ```
2. All existing tests (8 original) pass with the updated mock data.
3. The 13 new tests pass.
4. Expected total: 21+ tests, 0 failures, 0 errors.
5. No test uses real database access (all use mocks).

---

## Phase 5: Refined Seed Data and Final Documentation [COMPLETED]

**Objective:** End-to-end verification of the complete system and final cleanup.

**Dependencies:** Phase 4 completed.

**Status:** Completed on 2026-04-14. E2E verification passed: seed-fresh works, all endpoints return correct data, soft-delete excludes from stats/list, 23/23 tests passing.

### Task 5.1: End-to-end verification

**What to do:**
1. `make clean` -- clean everything.
2. `make build && make start` -- rebuild.
3. `make migrate` -- apply migrations.
4. `make seed` -- load seed data.
5. Manually verify with curl or Swagger:
   - `GET /courses` returns 3 courses with rating stats.
   - `GET /courses/curso-de-react` returns detail with rating stats.
   - `POST /courses/curso-de-react/ratings` creates a new rating.
   - `POST /courses/curso-de-react/ratings` with the same user_identifier updates.
   - `GET /courses/curso-de-react/ratings` returns the list.
   - `GET /courses/curso-de-react/ratings/stats` reflects the new rating.
   - `DELETE /ratings/{id}?user_identifier=<uuid>` soft-deletes the rating.
   - The deleted rating no longer appears in the list and does not affect the stats.

### Task 5.2: Validate that there are no regressions in existing clients

**What to do:**
- Verify that the frontends (Next.js, Android, iOS) DO NOT break due to the additional `average_rating` and `ratings_count` fields in the courses responses.
- The additional fields are additive (they are added, not modified or removed from existing fields), so clients should ignore them if they do not use them.

### Phase 5 Verification Criteria

1. The app starts clean without errors.
2. All existing endpoints continue working.
3. The new ratings endpoints work correctly.
4. Tests pass: `uv run pytest app/test_main.py -v`.
5. The seed data is consistent: the calculated stats match the inserted ratings.

---

## File Summary by Phase

| Phase | New Files | Modified Files |
|-------|-----------|----------------|
| 1 | `models/rating.py` | `models/__init__.py`, `models/course.py`, `db/seed.py`, + autogenerated migration |
| 2 | `schemas/__init__.py`, `schemas/rating.py`, `services/rating_service.py` | `services/__init__.py`, `services/course_service.py` |
| 3 | (none) | `main.py`, `specs/00_contracts.md` |
| 4 | (none) | `test_main.py` |
| 5 | (none) | (none, verification only) |

**Totals:** 4 new files, 8 modified files, 1 autogenerated migration.

---

## Execution Order with Human Validations

```
Phase 1: Model + Migration + Seed
  --> PAUSE: verify that the table exists and seed works
Phase 2: Schemas + Service + Modify CourseService
  --> PAUSE: verify that GET /courses returns rating stats
Phase 3: API Endpoints + Contracts
  --> PAUSE: verify the 4 endpoints manually
Phase 4: Tests
  --> PAUSE: verify that all tests pass
Phase 5: E2E Verification
  --> COMPLETE
```

Each phase can be aborted and reverted without affecting the previous ones. Phase 1 is the only one that modifies the database schema and requires special care with rollback (revert migration with `alembic downgrade -1`).
