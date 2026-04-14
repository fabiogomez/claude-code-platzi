# CLAUDE.md — PlatziFlix

## Project Overview

PlatziFlix is an educational video streaming platform (Netflix-style for courses). The repository is a **monorepo** containing 4 independent projects that share a single REST API backend.

## Architecture

```
Frontend (Next.js) ──┐
Android (Compose)  ──┼──► REST API (FastAPI) ──► PostgreSQL 15
iOS (SwiftUI)      ──┘
```

## Projects

### Backend (`Backend/`)

#### Stack & Dependencies

| Package | Version | Purpose |
|---|---|---|
| Python | >=3.11 | Runtime (Docker: `python:3.11-slim`) |
| FastAPI | 0.115.12 | Web framework |
| Uvicorn | 0.34.3 | ASGI server (with `--reload` in dev) |
| SQLAlchemy | 2.0.41 | ORM |
| Alembic | 1.16.1 | Database migrations |
| Pydantic | 2.11.5 | Data validation (transitive via FastAPI) |
| Pydantic Settings | 2.9.1 | Configuration management |
| psycopg2-binary | 2.9.10 | PostgreSQL driver |
| Pytest | 8.4.0 | Testing (dev dependency) |

- **Package manager**: uv
- **Database**: PostgreSQL 15 via Docker
- **Port**: 8000

#### Architecture Pattern

Simplified layered architecture (no repository layer, no router separation):

```
Routes (main.py)  --Depends()--> Service Layer (course_service.py) --ORM--> Models --Engine--> PostgreSQL
```

- All routes defined directly on the `app` instance in `main.py` (no `APIRouter`).
- Services receive `db: Session` via constructor injection. Instantiated per-request via `Depends()`.
- No Pydantic response schemas — endpoints return raw `dict`/`list`.
- No CORS middleware configured.

#### Project Structure

```
Backend/
├── Dockerfile                    # Python 3.11-slim, uv, hot-reload uvicorn
├── docker-compose.yml            # 2 services: db (postgres:15), api (FastAPI)
├── Makefile                      # Dev workflow commands
├── pyproject.toml / uv.lock      # Dependencies
├── app/
│   ├── main.py                   # FastAPI app, route definitions, DI wiring
│   ├── test_main.py              # Pytest tests with mock service injection
│   ├── alembic.ini               # Alembic config
│   ├── core/
│   │   └── config.py             # Settings (Pydantic BaseSettings, env: DATABASE_URL)
│   ├── db/
│   │   ├── base.py               # create_engine, SessionLocal, get_db() generator
│   │   └── seed.py               # create_sample_data() + clear_all_data()
│   ├── models/
│   │   ├── base.py               # Base = declarative_base(), BaseModel (id, timestamps, soft delete)
│   │   ├── teacher.py            # Teacher (name, email unique)
│   │   ├── course.py             # Course (name, description, thumbnail, slug unique)
│   │   ├── lesson.py             # Lesson (course_id FK, name, description, slug, video_url)
│   │   ├── course_teacher.py     # course_teachers junction Table (composite PK)
│   │   ├── class.py              # DEAD CODE — unused duplicate of Lesson
│   │   └── __init__.py           # Re-exports all models
│   ├── services/
│   │   ├── course_service.py     # CourseService: get_all_courses(), get_course_by_slug()
│   │   └── __init__.py
│   └── alembic/
│       ├── env.py                # Imports all models for autogenerate
│       └── versions/             # Migration files
└── specs/
    ├── 00_contracts.md           # API entity shapes + endpoint contracts
    └── 01_setup.md               # Setup guide
```

#### Database Layer (`app/db/base.py`)

```python
engine = create_engine(settings.database_url)  # Default QueuePool (pool_size=5)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:  # Yields Session, closes in finally. Does NOT commit.
```

- DB URL in Docker: `postgresql://platziflix_user:platziflix_password@db:5432/platziflix_db`
- Default fallback: `postgresql://user:password@localhost:5432/platziflix`

#### BaseModel (`app/models/base.py`)

All entities inherit from `BaseModel`:

```python
class BaseModel(Base):
    __abstract__ = True
    id         = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
```

Soft delete filtering is **manual** per query (`deleted_at.is_(None)`), not automatic.

#### Models

| Model | Table | Key Fields | Relationships |
|---|---|---|---|
| Teacher | `teachers` | name, email (unique, indexed) | M:N with Course via `course_teachers` |
| Course | `courses` | name, description, thumbnail, slug (unique, indexed) | M:N with Teacher, 1:N with Lesson |
| Lesson | `lessons` | course_id (FK), name, description, slug, video_url | M:1 with Course |
| course_teachers | `course_teachers` | course_id + teacher_id (composite PK) | Junction table (SQLAlchemy `Table`, not ORM model) |

**Note**: `app/models/class.py` contains a dead `Class` model (table `classes`) never imported/migrated/used.

#### Service Layer (`app/services/course_service.py`)

```python
class CourseService:
    def __init__(self, db: Session): ...
    def get_all_courses(self) -> List[Dict[str, Any]]:     # Returns [{id, name, description, thumbnail, slug}]
    def get_course_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:  # Returns {id, name, ..., teacher_id: [int], classes: [{id, name, description, slug}]}
```

- Uses `joinedload` for eager loading teachers and lessons.
- Returns `"classes"` key in response (mapped from `course.lessons`).
- Returns `"teacher_id": [int]` (list of IDs, not teacher objects).
- Filters soft-deleted lessons in Python (list comprehension), not SQL.

#### API Endpoints

| Method | Path | Response Shape |
|---|---|---|
| `GET /` | | `{"message": "Bienvenido a Platziflix API"}` |
| `GET /health` | | `{status, service, version, database: bool, courses_count?}` |
| `GET /courses` | | `[{id, name, description, thumbnail, slug}]` |
| `GET /courses/{slug}` | | `{id, name, description, thumbnail, slug, teacher_id: [int], classes: [{id, name, description, slug}]}` or 404 |

**Missing**: `GET /courses/:slug/classes/:id` is in contracts but not implemented.

#### Testing (`app/test_main.py`)

- **Pattern**: Mock `CourseService` via `app.dependency_overrides`, assert on `TestClient` responses.
- **Fixture**: `Mock(spec=CourseService)` — strict mock matching service interface.
- **Test classes**: `TestRootEndpoint`, `TestHealthEndpoint`, `TestCoursesEndpoints`, `TestContractCompliance`.
- **Contract tests** verify exact field sets (no extra fields allowed).
- **Gap**: Health endpoint uses `engine.connect()` directly — not mockable via DI.

#### Makefile Commands

| Command | Action |
|---|---|
| `make start` | `docker-compose up -d` |
| `make stop` | `docker-compose down` |
| `make restart` | `docker-compose restart` |
| `make build` | `docker-compose build` |
| `make logs` | `docker-compose logs -f` |
| `make clean` | Down + remove volumes, images, orphans |
| `make migrate` | `alembic upgrade head` inside container |
| `make create-migration` | Interactive prompt + `alembic revision --autogenerate` |
| `make seed` | `python -m app.db.seed` inside container |
| `make seed-fresh` | Clear all data + re-seed |

#### Known Architecture Gaps

1. **Dead code**: `app/models/class.py` — unused duplicate of Lesson model
2. **No CORS** — browser client-side fetches would be blocked
3. **No Pydantic response schemas** — no auto OpenAPI docs, no output validation
4. **No `APIRouter`** — all routes on single `app` instance
5. **Health endpoint bypasses DI** — uses `engine.connect()` directly, not testable via mocks
6. **`datetime.utcnow()` deprecated** — should use `datetime.now(timezone.utc)`
7. **`declarative_base()` deprecated** — SQLAlchemy 2.0 recommends `DeclarativeBase`
8. **Naming mismatch**: ORM uses `Lesson`/`lessons`, API returns `"classes"`, frontend types use `Class`
9. **Missing endpoint**: `GET /courses/:slug/classes/:id` defined in contract but not implemented
10. **No global error handler** — unhandled exceptions return default 500

### Frontend (`Frontend/`)
- **Stack**: Next.js 15.3.3 (App Router), React 19, TypeScript, SASS/SCSS Modules
- **Package manager**: Yarn
- **Port**: 3000 (default)
- **Structure**:
  - `src/app/page.tsx` — Home page (course listing)
  - `src/app/course/[slug]/page.tsx` — Course detail (with error.tsx, loading.tsx, not-found.tsx)
  - `src/app/classes/[class_id]/page.tsx` — Video player page
  - `src/components/` — Course, CourseDetail, VideoPlayer
  - `src/types/index.ts` — TypeScript interfaces (Course, Class, CourseDetail)
  - `src/styles/` — reset.scss, vars.scss (auto-imported via next.config.ts)
  - `docs/` — BDD feature file (Gherkin)
- **Data fetching**: Server Components with `fetch()`, `cache: "no-store"`, hitting `http://localhost:8000`
- **Testing**: Vitest + React Testing Library (`*.test.tsx` files colocated)
- **No state management library** — props-based data flow

### Android (`Mobile/PlatziFlixAndroid/`)
- **Stack**: Kotlin, Jetpack Compose, Material3
- **Architecture**: MVVM + Clean Architecture
- **Networking**: Retrofit 2.9.0 + OkHttp 4.12.0 + Gson
- **Image loading**: Coil 2.5.0
- **Async**: Coroutines 1.7.3
- **State**: StateFlow + sealed classes for UI events
- **API base URL**: `http://10.0.2.2:8000/` (Android emulator localhost)
- **Package**: `com.espaciotiago.platziflixandroid`
- **Structure**:
  - `data/` — DTOs, Mappers, Network (ApiService, RetrofitClient), Repository impl
  - `domain/` — Business models, Repository interfaces
  - `presentation/courses/` — Screens, Components, ViewModel, UiState
  - `ui/theme/` — Color, Spacing, Typography, Theme

### iOS (`Mobile/PlatziFlixiOS/`)
- **Stack**: Swift, SwiftUI
- **Architecture**: MVVM + Clean Architecture
- **Networking**: Custom URLSession-based NetworkManager (async/await)
- **State**: @Published + Combine
- **API base URL**: `http://localhost:8000`
- **Structure**:
  - `Data/` — DTOs, Mappers, Repository implementations
  - `Domain/` — Business models, Repository protocols
  - `Presentation/` — ViewModels, SwiftUI Views
  - `Services/` — NetworkManager, APIEndpoint, HTTPMethod, NetworkError

## Data Model

```
Teacher ←N:M→ Course (via course_teachers) ←1:N→ Lesson
```

- **Teacher**: id, name, email (unique), timestamps, soft delete
- **Course**: id, name, description, thumbnail, slug (unique), timestamps, soft delete
- **Lesson**: id, course_id (FK), name, description, slug, video_url, timestamps, soft delete
- **course_teachers**: course_id + teacher_id (composite PK)

All entities use soft delete (`deleted_at`) and automatic timestamps (`created_at`, `updated_at`).

## Shared Patterns

- **DTO → Domain mapping** in all clients and backend service layer
- **Slug-based routing** instead of numeric IDs
- **Loading/Error/Empty states** in all 3 client UIs
- **No authentication** implemented in any layer
- **No external state management** (no Redux, Zustand, etc.)

## Infrastructure

Only the backend is containerized (Docker Compose):
- **api** service: FastAPI with hot-reload, volumes for `app/` and `specs/`
- **db** service: PostgreSQL 15 with persistent volume
- Credentials: `platziflix_user` / `platziflix_password` / `platziflix_db`

## Development Workflow

```bash
# Backend
cd Backend
make start          # Start API + DB containers
make seed           # Populate sample data
make migrate        # Run Alembic migrations
make logs           # View container logs

# Frontend
cd Frontend
yarn install
yarn dev            # Start Next.js dev server (Turbopack)
yarn test           # Run Vitest

# Mobile
# Android: Open PlatziFlixAndroid/ in Android Studio
# iOS: Open PlatziFlixiOS/ in Xcode
```
