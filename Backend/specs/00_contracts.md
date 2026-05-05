# Platziflix

plataforma online de cursos, cada cursos tiene clases, descripciones y no hay mucho mas, eso es el inicio.

## Stacks

### Frontend
- Typescript
- CSS modules
- SASS

### Mobile
- iOS:
    - Swift
    - SwiftUI
- Android:
    - Kotlin
    - Jetpack Compose

### Backend
- Python
- FastAPI
- PostgreSQl

## Contratos

### Entidades
1. Curso
2. Clases
3. Profesor
4. Rating

### Contratos


- Course
```json
{
    "id": 1,
    "name": "Curso de React",
    "description": "Curso de React",
    "thumbnail": "https://via.placeholder.com/150", 
    "slug": "curso-de-react",
    "created_at": "2021-01-01",
    "updated_at": "2021-01-01",
    "deleted_at": "2021-01-01",
    "teacher_id": [1, 2, 3]
}
```

- Clases:
```json
{
    "id": 1, 
    "course_id": 1, 
    "name": "Clase 1",
    "description": "Clase 1",
    "slug": "clase-1",
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "created_at": "2021-01-01",
    "updated_at": "2021-01-01",
    "deleted_at": "2021-01-01"
}
```

- Teacher
```json
{
    "id": 1,
    "name": "John Doe",
    "email": "john.doe@example.com",
    "created_at": "2021-01-01",
    "updated_at": "2021-01-01",
    "deleted_at": "2021-01-01"
}
```

- Rating
```json
{
    "id": 1,
    "course_id": 1,
    "user_identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "score": 5,
    "comment": "Excellent course!",
    "created_at": "2021-01-01T00:00:00",
    "updated_at": "2021-01-01T00:00:00"
}
```

### Endpoints

- GET /courses -> Listar todos los cursos
```json
[
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
```

- GET /courses/:slug -> Obtener un curso
```json
{
    "id": 1,
    "name": "Curso de React",
    "description": "Curso de React",
    "thumbnail": "https://via.placeholder.com/150", 
    "slug": "curso-de-react",
    "teacher_id": [1, 2, 3],
    "classes": [
        {
            "id": 1,
            "name": "Clase 1",
            "description": "Clase 1",
            "slug": "clase-1",
        }
    ],
    "average_rating": 4.5,
    "ratings_count": 2
}
```
- GET /courses/:slug/classes/:id -> Obtener una clase
```json
{
    "id": 1,
    "name": "Clase 1",
    "description": "Clase 1",
    "slug": "clase-1",
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "created_at": "2021-01-01",
    "updated_at": "2021-01-01",
    "deleted_at": "2021-01-01"
}
```

- POST /courses/:slug/ratings -> Create or update a rating
```json
// Request body
{
    "score": 5,
    "user_identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "comment": "Excellent course!"
}

// Response (201)
{
    "id": 1,
    "course_id": 1,
    "user_identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "score": 5,
    "comment": "Excellent course!",
    "created_at": "2021-01-01T00:00:00",
    "updated_at": "2021-01-01T00:00:00"
}
```

- GET /courses/:slug/ratings -> List ratings for a course
```json
[
    {
        "id": 1,
        "course_id": 1,
        "user_identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "score": 5,
        "comment": "Excellent course!",
        "created_at": "2021-01-01T00:00:00",
        "updated_at": "2021-01-01T00:00:00"
    }
]
```

- GET /courses/:slug/ratings/stats -> Get rating statistics for a course
```json
{
    "average_rating": 4.5,
    "ratings_count": 2
}
```

- DELETE /ratings/:rating_id?user_identifier=<uuid> -> Soft-delete a rating
```json
{
    "message": "Rating deleted successfully"
}
```
