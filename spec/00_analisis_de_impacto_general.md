# Analisis Tecnico de Impacto: PlatziFlix

**Fecha:** 2026-03-30
**Branch:** `start-zero`
**Autor:** Arquitecto de Software (Claude Opus 4.6)

---

## 1. Estado Actual de Cada Componente

### 1.1 Backend (FastAPI + PostgreSQL)

**Estado: Funcional con deuda tecnica significativa**

**Lo que existe:**
- FastAPI configurada con 4 endpoints: `GET /`, `GET /health`, `GET /courses`, `GET /courses/{slug}`
- SQLAlchemy 2.0 con modelos: `Teacher`, `Course`, `Lesson`, tabla de asociacion `course_teachers`
- Alembic con 1 migracion inicial que crea el esquema completo (teachers, courses, lessons, course_teachers)
- Seed con 3 profesores, 3 cursos y 6 lecciones
- Tests unitarios con mocks (13 tests en `test_main.py`)
- Docker Compose con PostgreSQL 15 + API con hot-reload
- Dependency injection via `get_course_service` -> `CourseService(db)`

**Problemas criticos detectados:**

1. **Modelo duplicado `Class` vs `Lesson`:** Existe un archivo `app/models/class.py` con un modelo `Class` (tablename `classes`) que es identico en estructura a `Lesson` (tablename `lessons`). Sin embargo:
   - `Class` NO esta exportado en `__init__.py`
   - `Class` NO tiene migracion (la tabla `classes` no existe en la BD)
   - El modelo `Course` tiene relacion con `lessons` (no con `classes`)
   - El servicio `CourseService` usa `course.lessons` pero renombra la clave a `"classes"` en el JSON de respuesta
   - Esto genera confusion: la tabla real es `lessons`, pero la API responde con `"classes"`

2. **Endpoint faltante:** El contrato (`00_contracts.md`) especifica `GET /courses/:slug/classes/:id` para obtener una clase individual con `video_url`, pero este endpoint NO esta implementado.

3. **Sin Pydantic response models:** Los endpoints retornan `dict` y `list` directamente en lugar de usar `BaseModel` de Pydantic, lo que significa:
   - Sin validacion automatica de respuesta
   - Sin documentacion OpenAPI tipada
   - Sin serializacion controlada

4. **`datetime.utcnow()` deprecado:** El `BaseModel` de SQLAlchemy usa `datetime.utcnow()` que esta deprecado desde Python 3.12. Deberia usar `datetime.now(UTC)`.

5. **`declarative_base()` deprecado:** SQLAlchemy 2.0 recomienda `DeclarativeBase` en lugar de `declarative_base()`.

6. **Sin CORS configurado:** No hay middleware CORS, lo que impedira que el Frontend (puerto 3000) consuma la API (puerto 8000) en navegador.

7. **Health check acoplado:** El endpoint `/health` ejecuta un query directo a la tabla `courses` en lugar de un simple `SELECT 1`, lo que lo acopla al estado de las migraciones.

---

### 1.2 Frontend (Next.js 15 + TypeScript)

**Estado: Estructura completa pero con desalineacion severa con la API**

**Lo que existe:**
- Next.js 15.3.3 con App Router y Turbopack
- 3 paginas: Home (`/`), Course Detail (`/course/[slug]`), Class Player (`/classes/[class_id]`)
- 3 componentes: `Course`, `CourseDetail`, `VideoPlayer`
- Error boundary, loading state y not-found para la pagina de curso
- Tests con Vitest + React Testing Library (3 archivos de test)
- SASS/SCSS Modules para estilos
- Server Components con fetch + `cache: "no-store"`

**Problemas criticos detectados:**

1. **Desalineacion total de tipos TypeScript con la API:**

   | Campo TypeScript    | Valor Frontend     | Valor API Real       | Estado     |
   |--------------------|--------------------|----------------------|------------|
   | `Course.title`     | `string`           | `name` (string)      | DESALINEADO |
   | `Course.teacher`   | `string`           | `teacher_id` (int[]) | DESALINEADO |
   | `Course.duration`  | `number`           | No existe            | INEXISTENTE |
   | `Class.title`      | `string`           | `name` (string)      | DESALINEADO |
   | `Class.video`      | `string`           | `video_url` (string) | DESALINEADO |
   | `Class.duration`   | `number`           | No existe            | INEXISTENTE |

2. **Fetch incorrecto en Home:** `getCourses()` accede a `data.data` (linea 12 de `page.tsx`), pero la API retorna un array plano `[{...}, {...}]`, no `{data: [...]}`. Esto causara un error en runtime.

3. **Tipos fantasma:** La interfaz `Progress`, `Quiz`, `QuizOption`, y `FavoriteToggle` en `types/index.ts` no corresponden a ningun endpoint o modelo del backend. Son features futuras que no deberian estar definidas aun.

4. **Endpoint inexistente para clases:** La pagina `/classes/[class_id]` hace fetch a `http://localhost:8000/classes/${class_id}`, pero este endpoint NO existe en el backend. Solo existe `GET /courses/{slug}` que incluye las clases embebidas.

5. **URL hardcodeada:** Todas las llamadas fetch usan `http://localhost:8000` directamente, sin variable de entorno configurable.

6. **`CourseDetail` espera `duration` en clases:** El componente calcula duracion total con `course.classes.reduce((acc, cls) => acc + cls.duration, 0)`, pero la API no devuelve `duration`.

---

### 1.3 Android (Kotlin + Jetpack Compose)

**Estado: Capa de lista de cursos funcional, sin navegacion ni detalle**

**Lo que existe:**
- Clean Architecture: Data (DTOs, Mappers, Repositories) -> Domain (Models, Repository interface) -> Presentation (ViewModel, Screens, Components)
- `CourseDTO` con mapping a `Course` domain model
- `ApiService` con Retrofit: solo `GET /courses`
- `RemoteCourseRepository` + `MockCourseRepository` para desarrollo
- `CourseListViewModel` con MVI pattern (UiState + UiEvents)
- `CourseListScreen` con estados: Loading, Error, Empty, Content
- `CourseCard` con Coil para carga de imagenes
- Manual DI via `AppModule` (sin Hilt/Koin)
- Tests unitarios para el ViewModel (5 tests)

**Problemas detectados:**

1. **Solo vista de lista:** No hay pantalla de detalle de curso ni reproductor de video.
2. **Sin navegacion:** `onCourseClick` tiene un TODO en `MainActivity` -- no hay Navigation Compose configurado.
3. **Sin endpoint de detalle:** `ApiService` solo define `getAllCourses()`, no hay `getCourseBySlug()` ni `getClassById()`.
4. **Sin DTO de detalle:** No hay `CourseDetailDTO` ni `ClassDTO` en el paquete de data.
5. **DI manual fragil:** `AppModule` es un singleton manual. A medida que crece, sera dificil de mantener vs. Hilt.

---

### 1.4 iOS (Swift + SwiftUI)

**Estado: El mas completo en arquitectura, pero solo implementa vista de lista**

**Lo que existe:**
- Clean Architecture: Data (DTOs, Mappers, Repositories) -> Domain (Models, Protocols) -> Presentation (ViewModels, Views)
- DTOs completos: `CourseDTO`, `CourseDetailDTO`, `ClassDTO`, `ClassDetailDTO`, `TeacherDTO`
- Domain models: `Course`, `Class`, `Teacher` con mock data para previews
- Mappers: `CourseMapper`, `ClassMapper`, `TeacherMapper`
- `NetworkManager` completo con protocol `NetworkService`, `APIEndpoint`, error handling (`NetworkError`)
- `CourseAPIEndpoints` con `getAllCourses` y `getCourseBySlug`
- `RemoteCourseRepository` implementando `CourseRepository` protocol
- `CourseListViewModel` con search, refresh, error handling
- `CourseListView` con search bar, pull-to-refresh, estados adaptativos
- `CourseCardView` con AsyncImage, dark mode, accesibilidad
- Design System completo: colores, spacing, radios, tipografia, CardStyle modifier
- Previews multiples: light/dark mode, iPhone SE, iPad

**Problemas detectados:**

1. **Sin navegacion a detalle:** `selectCourse()` solo imprime al console -- no hay NavigationLink ni vista de detalle.
2. **Sin vista de clases/video:** Aunque los DTOs y modelos para clases existen, no hay UI para mostrarlos.
3. **`CourseRepository` protocol tiene metodos de detalle** (`getCourseBySlug`) que estan implementados en `RemoteCourseRepository` pero nunca se llaman desde el ViewModel.
4. **Base URL diferente entre plataformas:** iOS usa `http://localhost:8000`, Android usa `http://10.0.2.2:8000/`. Esto es correcto para emuladores pero no configurable para produccion.

---

## 2. Dependencias entre Componentes

```
                    +-------------------+
                    |   API Contracts   |
                    | (00_contracts.md) |
                    +---------+---------+
                              |
               Definido pero no validado
                              |
                    +---------+---------+
                    |     Backend       |
                    |   FastAPI + PG    |
                    |   Puerto: 8000    |
                    +---------+---------+
                              |
              +---------------+---------------+
              |               |               |
     +--------+--------+  +--+---+  +--------+--------+
     |   Frontend       |  |Android|  |      iOS        |
     |   Next.js        |  |Compose|  |    SwiftUI      |
     |   Puerto: 3000   |  | :8000 |  |    :8000        |
     +------------------+  +-------+  +-----------------+
```

### Cadena de dependencias critica:

1. **Backend es el cuello de botella:** Los 3 clientes dependen del Backend. Cualquier cambio en la API requiere coordinacion con los 3 frontends.

2. **Contratos como fuente de verdad:** El archivo `00_contracts.md` deberia ser la referencia, pero actualmente:
   - El Backend implementa parcialmente (falta `GET /courses/:slug/classes/:id`)
   - El Frontend tiene tipos que no coinciden con los contratos
   - Android solo consume `GET /courses`
   - iOS tiene DTOs alineados pero no consume el detalle

3. **Sin versionado de API:** No hay prefijo `/v1/` ni mecanismo de versionado, lo que hara dificil evolucionar la API sin romper clientes.

---

## 3. Puntos de Integracion Criticos

### 3.1 Integracion Backend <-> Frontend (ROTA)

| Punto de Falla | Descripcion | Severidad |
|----------------|-------------|-----------|
| `data.data` en getCourses | Frontend espera `{data: [...]}`, API retorna `[...]` | **CRITICA** - App no cargara |
| Campos `title` vs `name` | Frontend usa `title`, API usa `name` | **CRITICA** - Datos no se muestran |
| Campo `teacher` (string) | Frontend espera string, API envia `teacher_id` (int[]) | **ALTA** - Info de profesor no funciona |
| Campo `duration` | Frontend requiere duration, API no lo provee | **ALTA** - Calculos fallan |
| Endpoint `/classes/{id}` | Frontend llama a endpoint que no existe | **CRITICA** - Pagina de clase no funciona |
| CORS | Sin middleware CORS configurado | **CRITICA** - Browser bloquea requests |

### 3.2 Integracion Backend <-> Android (PARCIAL)

| Punto | Estado | Nota |
|-------|--------|------|
| `GET /courses` | Funcional | DTO alineado con respuesta real |
| `GET /courses/{slug}` | No implementado en cliente | Sin endpoint definido en ApiService |
| `GET /classes/{id}` | No implementado en ninguno | Ni backend ni cliente |

### 3.3 Integracion Backend <-> iOS (PARCIAL)

| Punto | Estado | Nota |
|-------|--------|------|
| `GET /courses` | Funcional | DTO alineado |
| `GET /courses/{slug}` | Preparado en cliente, funcional en backend | No se llama desde UI |
| `GET /classes/{id}` | DTO preparado, endpoint no existe en backend | ClassDetailDTO listo pero sin uso |

---

## 4. Deuda Tecnica y Riesgos

### 4.1 Deuda Tecnica por Componente

| # | Componente | Item | Impacto | Esfuerzo |
|---|-----------|------|---------|----------|
| 1 | Backend | Modelo Class duplicado sin uso | Confusion en equipo | Bajo |
| 2 | Backend | Sin Pydantic response models | Sin validacion/docs | Medio |
| 3 | Backend | Endpoint de clase individual faltante | Feature incompleta | Medio |
| 4 | Backend | Sin CORS | Frontend no funciona | Bajo |
| 5 | Backend | APIs deprecadas (utcnow, declarative_base) | Warning/compat futuro | Bajo |
| 6 | Frontend | Tipos desalineados con API | App rota | Alto |
| 7 | Frontend | `data.data` en fetch | Home page rota | Bajo |
| 8 | Frontend | URL hardcodeada | No desplegable | Bajo |
| 9 | Frontend | Tipos fantasma (Progress, Quiz, Favorite) | Confusion | Bajo |
| 10 | Android | Sin navegacion | Solo 1 pantalla | Alto |
| 11 | Android | Sin DI framework | Escalabilidad | Medio |
| 12 | iOS | Sin navegacion a detalle | Solo 1 pantalla | Alto |
| 13 | Todos | Sin versionado de API | Riesgo en evolucion | Medio |
| 14 | Todos | Sin autenticacion | Sin perfiles de usuario | Alto |

### 4.2 Riesgos Arquitecturales

1. **Riesgo de divergencia:** Cada cliente tiene su propia interpretacion de los datos. Sin un mecanismo de validacion automatica (schema compartido, contract testing), los clientes divergiran mas con cada feature.

2. **Riesgo de acoplamiento temporal:** El Frontend usa Server Components con `cache: "no-store"`, lo que significa que cada pageview hace un request al backend. Si el backend cae, el frontend cae completamente (sin fallback).

3. **Riesgo de datos inconsistentes:** El seed usa el modelo `Lesson` pero la respuesta de la API nombra el campo como `"classes"`. Si un desarrollador crea una migracion, podria crear una tabla `classes` que coexista con `lessons`.

---

## 5. Plan de Implementacion

### Fase 0: Estabilizacion Critica (Prioridad URGENTE)

**Objetivo:** Hacer que la integracion Backend-Frontend funcione end-to-end.

#### Tarea 0.1: Agregar CORS al Backend
- **Archivo:** `Backend/app/main.py`
- **Cambio:** Agregar `CORSMiddleware` de FastAPI permitiendo `http://localhost:3000`
- **Dependencias:** Ninguna
- **Esfuerzo:** 15 minutos
- **Test:** Verificar que el Frontend pueda hacer requests al Backend desde el browser

#### Tarea 0.2: Eliminar el modelo Class duplicado
- **Archivo:** `Backend/app/models/class.py` -- ELIMINAR
- **Cambio:** Remover `class.py` del directorio de modelos. El modelo `Lesson` es el correcto y ya esta en uso.
- **Dependencias:** Ninguna
- **Esfuerzo:** 5 minutos

#### Tarea 0.3: Alinear tipos del Frontend con la API
- **Archivo:** `Frontend/src/types/index.ts`
- **Cambios:**
  ```typescript
  export interface Course {
    id: number;
    name: string;        // era "title"
    description: string;
    thumbnail: string;
    slug: string;
  }

  export interface Class {
    id: number;
    name: string;        // era "title"
    description: string;
    slug: string;
  }

  export interface CourseDetail extends Course {
    teacher_id: number[];  // era "teacher" string
    classes: Class[];
  }
  ```
- **Impacto cascada:** Requiere actualizar TODOS los componentes que usan `title`, `teacher`, `duration`, `video`
- **Esfuerzo:** 2-3 horas
- **Test:** Actualizar tests de componentes

#### Tarea 0.4: Corregir fetch en Home page
- **Archivo:** `Frontend/src/app/page.tsx`
- **Cambio:** Cambiar `return data.data` a `return data` (la API retorna array directo)
- **Esfuerzo:** 5 minutos
- **Test:** Verificar que la pagina Home carga los cursos

#### Tarea 0.5: Configurar variable de entorno para API URL
- **Archivos:** `Frontend/.env.local` (nuevo), todos los archivos con fetch
- **Cambio:** Usar `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`
- **Esfuerzo:** 30 minutos

---

### Fase 1: Completar el Flujo Core (1-2 semanas)

**Objetivo:** Implementar el flujo completo: Lista de cursos -> Detalle -> Reproducir clase.

#### Tarea 1.1: Implementar endpoint `GET /courses/{slug}/classes/{id}` en Backend
- **Archivos:**
  - `Backend/app/services/course_service.py` -- agregar `get_class_by_id()`
  - `Backend/app/main.py` -- agregar endpoint
- **Contrato (de `00_contracts.md`):**
  ```json
  {
    "id": 1,
    "name": "Clase 1",
    "description": "Clase 1",
    "slug": "clase-1",
    "video_url": "https://...",
    "created_at": "2021-01-01",
    "updated_at": "2021-01-01",
    "deleted_at": "2021-01-01"
  }
  ```
- **Esfuerzo:** 2-3 horas
- **Test:** Agregar tests unitarios para el nuevo endpoint

#### Tarea 1.2: Crear Pydantic response models en Backend
- **Archivo:** `Backend/app/schemas/` (nuevo directorio)
  - `course.py`: `CourseListResponse`, `CourseDetailResponse`, `ClassResponse`
  - `teacher.py`: `TeacherResponse`
- **Beneficios:** Validacion automatica, OpenAPI docs tipadas, serializacion controlada
- **Esfuerzo:** 3-4 horas

#### Tarea 1.3: Adaptar Frontend para el flujo completo
- **Archivos a modificar:**
  - `src/components/Course/Course.tsx` -- usar `name` en lugar de `title`, remover `teacher`/`duration`
  - `src/components/CourseDetail/CourseDetail.tsx` -- adaptar a la estructura real de la API
  - `src/app/classes/[class_id]/page.tsx` -- cambiar URL del fetch al endpoint correcto
  - `src/components/VideoPlayer/VideoPlayer.tsx` -- usar `video_url` en lugar de `video`
- **Esfuerzo:** 1 dia

#### Tarea 1.4: Implementar navegacion en Android
- **Archivos nuevos:**
  - `data/entities/CourseDetailDTO.kt`, `ClassDTO.kt`
  - `data/mappers/ClassMapper.kt`
  - `data/network/ApiService.kt` -- agregar `getCourseBySlug()`, `getClassById()`
  - `presentation/coursedetail/` -- Screen, ViewModel, UiState
  - `presentation/classplayer/` -- Screen con video player
  - `navigation/NavGraph.kt` -- Navigation Compose
- **Dependencias:** Tareas 1.1 (endpoint de clase), agregar Navigation Compose dependency
- **Esfuerzo:** 3-5 dias

#### Tarea 1.5: Implementar navegacion en iOS
- **Archivos nuevos/modificados:**
  - `Presentation/Views/CourseDetailView.swift`
  - `Presentation/Views/ClassPlayerView.swift`
  - `Presentation/ViewModels/CourseDetailViewModel.swift`
  - `CourseListView.swift` -- agregar NavigationLink
- **Dependencias:** Tarea 1.1
- **Esfuerzo:** 2-3 dias (iOS ya tiene DTOs y repository preparados)

---

### Fase 2: Robustez y Calidad (2-3 semanas)

#### Tarea 2.1: Contract Testing
- Implementar tests que validen que la respuesta del backend coincide con los contratos definidos
- Herramientas sugeridas: `schemathesis` para el backend, validacion de schema JSON en clientes

#### Tarea 2.2: Pydantic Schemas compartidos
- Definir schemas Pydantic como fuente de verdad
- Generar JSON Schema automaticamente para uso de clientes moviles

#### Tarea 2.3: Mejorar error handling en Backend
- Estandarizar respuestas de error con formato consistente
- Agregar logging estructurado

#### Tarea 2.4: Mejorar testing
- Backend: Agregar tests de integracion con base de datos real (no solo mocks)
- Frontend: Agregar tests E2E con Playwright o Cypress
- Android: Expandir tests del ViewModel, agregar tests de UI con Compose Test
- iOS: Agregar XCTests para ViewModels y repository

#### Tarea 2.5: Actualizar APIs deprecadas del Backend
- Migrar de `declarative_base()` a `DeclarativeBase` (SQLAlchemy 2.0)
- Reemplazar `datetime.utcnow()` con `datetime.now(timezone.utc)`

---

### Fase 3: Features de Producto (4+ semanas)

#### Tarea 3.1: Autenticacion
- Implementar JWT auth en el backend
- Agregar login/registro en todos los clientes
- Definir roles basicos (estudiante, profesor, admin)

#### Tarea 3.2: Progreso del estudiante
- Nuevo modelo: `Progress` (user_id, class_id, seconds_watched, completed)
- Nuevos endpoints: `POST /progress`, `GET /courses/{slug}/progress`
- UI: barra de progreso en cada clase

#### Tarea 3.3: Busqueda de cursos
- Backend: Endpoint `GET /courses?q=search_term` con busqueda full-text
- Frontend/Mobile: UI de busqueda (iOS ya tiene la infraestructura con `searchText`)

#### Tarea 3.4: Favoritos
- Nuevo modelo: `Favorite` (user_id, course_id)
- CRUD de favoritos
- Requiere autenticacion (Tarea 3.1)

---

## 6. Orden Optimo de Desarrollo

```
Semana 1:
  [Backend]  Tarea 0.1 (CORS) ──────────────────────┐
  [Backend]  Tarea 0.2 (Eliminar Class duplicado) ───┤
  [Frontend] Tarea 0.3 (Alinear tipos) ──────────────┤──> INTEGRACION FUNCIONAL
  [Frontend] Tarea 0.4 (Corregir fetch) ─────────────┤
  [Frontend] Tarea 0.5 (Env vars) ───────────────────┘

Semana 2:
  [Backend]  Tarea 1.1 (Endpoint clase individual) ──┐
  [Backend]  Tarea 1.2 (Pydantic schemas) ───────────┤──> API COMPLETA
  [Frontend] Tarea 1.3 (Adaptar flujo completo) ─────┘

Semanas 3-4:
  [Android]  Tarea 1.4 (Navegacion + detalle + clase)
  [iOS]      Tarea 1.5 (Navegacion + detalle + clase)
  [Todos]    Tarea 2.1 (Contract testing)

Semanas 5-6:
  [Backend]  Tarea 2.3 (Error handling)
  [Backend]  Tarea 2.5 (APIs deprecadas)
  [Todos]    Tarea 2.4 (Testing expandido)

Semanas 7+:
  Fase 3 (Features de producto)
```

---

## 7. Resumen Ejecutivo

PlatziFlix tiene una arquitectura solida a nivel de diseno (Clean Architecture en los 3 clientes, separacion de capas en el backend), pero la **implementacion tiene gaps criticos de integracion**. El problema mas urgente es que **la integracion Backend-Frontend esta rota** debido a 6 puntos de falla simultaneos (CORS, formato de respuesta, campos desalineados, endpoint faltante).

Las 5 tareas de la Fase 0 son las de mayor impacto con el menor esfuerzo -- corregirlas permitira tener una demo funcional end-to-end. Los clientes moviles estan en mejor posicion (sus DTOs estan mas alineados con la API), pero ambos necesitan navegacion para completar el flujo de usuario.

**Prioridad inmediata:** Ejecutar Fase 0 completa antes de cualquier nueva feature.
