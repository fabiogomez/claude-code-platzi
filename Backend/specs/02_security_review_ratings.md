# Security Review: Ratings System

**Date:** 2026-04-14
**Reviewer:** Security Review (Claude Opus 4.6)
**Scope:** All changes on branch `start-zero` related to the ratings feature (Phases 1-5)

---

## Summary

One high-severity vulnerability was identified with a confidence of 9/10. The remaining findings were filtered out as functional bugs, design considerations, or excluded categories (DoS, rate limiting).

---

## Vuln 1: Broken Access Control — Any User Can Delete Any Rating

**Severity:** High
**Confidence:** 9/10
**Category:** `broken_access_control` (OWASP A01:2021, CWE-639)

**Affected files:**
- `Backend/app/main.py` lines 135-147 (`DELETE /ratings/{rating_id}` endpoint)
- `Backend/app/services/rating_service.py` lines 76-105 (`get_ratings_by_course` exposes `user_identifier`)
- `Backend/app/services/rating_service.py` lines 139-164 (`delete_rating` trusts client-supplied identifier)

### Description

The `DELETE /ratings/{rating_id}` endpoint relies solely on a client-supplied `user_identifier` query parameter for authorization. The `GET /courses/{slug}/ratings` endpoint publicly exposes `user_identifier` for every rating in its response. This means any caller can read a victim's `user_identifier` from the public listing, then use it to delete that victim's rating — no authentication or proof of identity required.

### Exploit Scenario

1. Attacker calls `GET /courses/curso-de-react/ratings` and observes rating `id: 8` with `user_identifier: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"`
2. Attacker calls `DELETE /ratings/8?user_identifier=a1b2c3d4-e5f6-7890-abcd-ef1234567890`
3. The rating is soft-deleted. The attacker had no prior knowledge of the identifier — it was served by the public API.

### Root Cause

```python
# main.py — DELETE endpoint accepts user_identifier from query param
@app.delete("/ratings/{rating_id}")
def delete_rating(
    rating_id: int,
    user_identifier: str,  # CLIENT SUPPLIES THIS — NO SERVER-SIDE VERIFICATION
    rating_service: RatingService = Depends(get_rating_service),
) -> dict:

# rating_service.py — delete_rating only checks if identifier matches the DB record
rating = (
    self.db.query(Rating)
    .filter(
        Rating.id == rating_id,
        Rating.user_identifier == user_identifier,  # MATCHES PUBLIC DATA
        Rating.deleted_at.is_(None),
    )
    .first()
)
```

The authorization check compares the client-supplied `user_identifier` against the stored value, but since the stored value is publicly readable via the GET endpoint, this provides no real access control.

### Recommendation

**Option A (quick mitigation):** Remove `user_identifier` from the `GET /courses/{slug}/ratings` response so the authorization token remains secret. This keeps the current authorization model but makes it harder to exploit.

**Option B (correct long-term fix):** Implement server-side authentication (JWT, OAuth2, or session-based) so the DELETE endpoint verifies the caller's identity independently of the request parameters. The `user_identifier` should be derived from the authenticated session, not from client input.

### Current Status

**Open** — Not yet remediated.

---

## Filtered Findings (Not Reported)

The following were identified during analysis but filtered out per review criteria:

| Finding | Reason for Exclusion |
|---|---|
| Soft-delete unique constraint bypass / race condition | Functional bug, not a security vulnerability (confidence 3/10) |
| `user_identifier` exposure as standalone information disclosure | Not PII; design characteristic of unauthenticated system (confidence 3/10) |
| No rate limiting on POST endpoint | Excluded category (DoS/resource exhaustion) |
| No pagination on GET ratings endpoint | Excluded category (resource exhaustion) |
| Missing database-level comment size constraint | Excluded category (resource exhaustion) |

---

## Positive Security Observations

- All database queries use SQLAlchemy ORM with parameterized queries — **no SQL injection risk**
- Input validation via Pydantic schemas enforces score range (1-5) and field constraints
- Database-level `CheckConstraint` on score provides defense-in-depth
- Soft-delete pattern preserves data integrity (no hard deletes)
