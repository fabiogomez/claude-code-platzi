---
name: PlatziFlix Architecture State - 2026-03-30
description: Comprehensive state of the PlatziFlix monorepo as analyzed for impact assessment - covers all 4 projects, critical gaps, and data model inconsistencies
type: project
---

PlatziFlix monorepo analyzed on 2026-03-30 from branch start-zero. Key findings:

1. Backend has a duplicate model problem: both Lesson and Class models exist with identical structure but the Class model is NOT exported in __init__.py and NOT used by the service layer. The seed uses Lesson, the API contract says "classes".
2. Frontend types are misaligned with the API contract: TypeScript interfaces use `title` instead of `name`, `teacher` (string) instead of `teacher_id` (int[]), `video` instead of `video_url`, and have `duration` which the API doesn't provide.
3. Frontend fetches `data.data` from /courses but the API returns a flat list, not `{data: [...]}`.
4. The contract specifies `GET /courses/:slug/classes/:id` but this endpoint is NOT implemented in the backend.
5. Android only implements course list view - no course detail or class view. No navigation.
6. iOS has DTOs for course detail and classes but only the course list view is implemented in the UI.
7. No authentication exists in any layer.

**Why:** This was the baseline assessment requested for impact analysis and implementation planning.
**How to apply:** Use this as the source of truth for what needs fixing before adding new features. Prioritize contract alignment across all layers.
