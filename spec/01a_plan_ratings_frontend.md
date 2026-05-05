# Frontend Implementation Plan: Ratings System

**Date:** 2026-04-06
**Base branch:** `start-zero`
**Author:** Frontend Specialist (Claude Opus 4.6)
**Reference document:** `spec/01_plan_ratings.md` (Architect Plan, Phase 5)

---

## Summary

This document breaks down Phase 5 of the architect's plan (Frontend) into sub-phases ordered by dependency, with specific tasks, exact paths, and verification criteria. Each phase is designed to be visually validated incrementally.

**External dependency:** Backend Phases 1-3 must be completed (functional ratings API at `http://localhost:8000`) before the integration phases (Phase F3 and F4) can be verified. Phases F1 and F2 can be developed in parallel with the backend.

---

## Discrepancies detected between the architect's plan and actual code

### Discrepancy 1: Type misalignment with the API (confirmed, pre-existing)

The `Course` type in `Frontend/src/types/index.ts` uses fields that do not match the actual backend API:

| Field in frontend (types) | Actual field in backend API |
|---------------------------|--------------------------|
| `title`                   | `name`                   |
| `teacher` (string)        | `teachers` (array of objects via M:N) |
| `duration` (number)       | Does not exist in Course |

This was already documented by the architect. The ratings plan adds `average_rating` and `ratings_count` on top of the current types without correcting this misalignment. This means the API currently does NOT return `title`, `teacher`, or `duration` in the course listing -- the frontend-backend integration is already broken before adding ratings. The architect's plan assumes this misalignment is resolved separately (Phase 0 of the impact analysis).

**Impact on the ratings plan:** If the misalignment is not resolved first, adding `average_rating` and `ratings_count` to the types will not be enough for the UI to work correctly. The `average_rating` and `ratings_count` fields returned by the API will be consumable, but the `title`, `teacher`, `duration` fields will still not work against the actual API.

**Recommendation:** Resolve the type misalignment BEFORE implementing the ratings system, or at least be aware that full visual verification requires the API data to match the types.

### Discrepancy 2: The slug `page.tsx` file does not pass `slug` as a prop

The architect indicates in Task 5.6 that we need to "pass slug as a prop for RatingForm" in `Frontend/src/app/course/[slug]/page.tsx`. However, the current code of that page passes the complete `courseData` object to `CourseDetailComponent`:

```typescript
return <CourseDetailComponent course={courseData} />;
```

The type `CourseDetail extends Course`, and `Course` already has `slug`. Therefore, `course.slug` is already available inside `CourseDetailComponent` and no additional slug prop is needed at the page level. The `RatingForm` can receive `courseSlug={course.slug}` directly from `CourseDetailComponent`. This simplifies the architect's Task 5.6: there is no need to modify `page.tsx` to pass slug.

### Discrepancy 3: The Course component does not need changes in page.tsx if spread is used

The architect (Task 5.7) suggests explicitly adding `average_rating` and `ratings_count` to the props in `page.tsx`. However, the current code already passes individual props (not spread). The architect's approach is correct: the two new props must be explicitly added to the JSX in `page.tsx`. This is not a discrepancy but rather a confirmation.

### Discrepancy 4: File count in the architect's summary

The summary says "4 new files" for frontend, but lists 5:
1. `Frontend/src/utils/userId.ts`
2. `Frontend/src/components/StarRating/StarRating.tsx`
3. `Frontend/src/components/StarRating/StarRating.module.scss`
4. `Frontend/src/components/RatingForm/RatingForm.tsx`
5. `Frontend/src/components/RatingForm/RatingForm.module.scss`

The correct count is 5 new frontend files.

### Discrepancy 5: No tests mentioned for new components

The architect only mentions updating the existing `Course.test.tsx` test, but does not include tests for `StarRating`, `RatingForm`, or `userId.ts`. Given that the project already has tests with Vitest + React Testing Library (3 existing test files), tests should be created for the new components to maintain coverage.

### Discrepancy 6: The Course test looks for "4.5 (10)" but StarRating renders "4.5 (10)" with HTML structure

The test proposed by the architect (`expect(screen.getByText("4.5 (10)"))`) assumes that the text "4.5 (10)" is rendered as a single text node. But reviewing the proposed StarRating component, the text is rendered inside a `<span className={styles.info}>` as `{average.toFixed(1)} ({count})`. This should work as a single text node, but we need to confirm there is no unexpected whitespace between the value and the parenthesis. The test should use `getByText(/4\.5/)` or similar if issues arise.

---

## Conventions observed in the current code

These conventions must be strictly followed during implementation:

1. **Type imports:** Use the `@/types` alias (e.g., `import { Course as CourseType } from "@/types"`)
2. **Style imports:** Use CSS Modules with `import styles from "./Component.module.scss"`
3. **SCSS imports:** Use `@import '../../styles/vars.scss'` at the top of each `.module.scss` (although `vars.scss` is auto-imported via `next.config.ts` with `prependData`, existing files also import it explicitly)
4. **color() function:** All colors are referenced via `color('name')` from the `$colors` map in `vars.scss`
5. **Functional components:** Exported as `const` with arrow functions. Some use `FC<Props>` (CourseDetail, VideoPlayer), others do not (Course)
6. **Naming:** Components in PascalCase, component files in PascalCase (`Course.tsx`, `CourseDetail.tsx`), directories in PascalCase (`Course/`, `CourseDetail/`)
7. **Tests:** Located in `__test__/` subdirectory (Course) or colocated with the component (VideoPlayer). They use `describe/it/expect` from Vitest and `render/screen` from RTL
8. **Server Components:** Are the default (no directive). Only `error.tsx` uses `"use client"`
9. **Data fetching:** Via `fetch()` with `cache: "no-store"` directly in pages (Server Components)
10. **Border radius:** Consistently `18px` for cards and containers, `12px` for internal elements, `8px` for small elements
11. **Shadows:** Pattern `0 6px 24px rgba(0,0,0,0.10)` for cards
12. **Typography weights:** `900` for hero titles, `800` for section titles, `700` for subtitles, `600` for labels

---

## Implementation Phases

### Phase F1: Types and Utilities (no backend dependency) [COMPLETED]

**Status:** COMPLETED - Types added to index.ts, userId utility created.

**Objective:** Establish the TypeScript type foundation and the anonymous user identification utility.

**Dependencies:** None. Can be done before the backend is ready.

---

#### Task F1.1: Add Rating types to the type system

**File:** `Frontend/src/types/index.ts`

**Changes:**
- Add `average_rating: number` and `ratings_count: number` to the `Course` interface (current lines 2-8). These fields are added as optional initially (`average_rating?: number` and `ratings_count?: number`) to avoid breaking existing components during the transition, or directly as required if updating everything at once is preferred.
- Add three new interfaces after `CourseDetail`:
  - `Rating`: with fields `id`, `course_id`, `user_identifier`, `score`, `comment` (string | null), `created_at`, `updated_at`
  - `RatingCreate`: with `score` (number), `user_identifier` (string), `comment` (optional string)
  - `RatingStats`: with `average_rating` (number) and `ratings_count` (number)

**Rationale:** Types are the foundation that enables strict typing across all new and modified components. They are added on top of the existing Course interface (keeping the misaligned fields `title`, `teacher`, `duration` unchanged).

---

#### Task F1.2: Create User ID utility

**File to create:** `Frontend/src/utils/userId.ts`

**Description:**
- Create directory `Frontend/src/utils/` (does not currently exist)
- Implement function `getUserId(): string` that:
  - Checks if running server-side (`typeof window === "undefined"`) and returns an empty string
  - Looks in `localStorage` with key `platziflix_user_id`
  - If it does not exist, generates a UUID with `crypto.randomUUID()` and persists it
  - Returns the UUID

**Rationale:** This is the anonymous identification piece that RatingForm needs to send ratings to the API. It should be a separate module for reusability and testability.

---

#### Verification criteria F1

1. `cd Frontend && yarn build` compiles without TypeScript errors
2. The types `Rating`, `RatingCreate`, `RatingStats` are exported and available
3. The `Course` type includes `average_rating` and `ratings_count`
4. The file `userId.ts` exports `getUserId`
5. `yarn test` passes (existing tests may fail if `average_rating`/`ratings_count` are marked as required -- this is resolved in F4)

---

### Phase F2: New Components (no backend dependency) [COMPLETED]

**Status:** COMPLETED - StarRating (Server Component) and RatingForm (Client Component) created with SCSS modules.

**Objective:** Create the StarRating and RatingForm components with their styles, ready for integration.

**Dependencies:** Phase F1 completed (types available).

---

#### Task F2.1: Create StarRating component (Server Component, read-only)

**File to create:** `Frontend/src/components/StarRating/StarRating.tsx`

**Description:**
- Create directory `Frontend/src/components/StarRating/`
- Functional component that receives props: `average` (number 0-5), `count` (number), `size` (optional, "sm" | "md", default "md")
- Do NOT include the `"use client"` directive -- it is a pure Server Component
- Uses `FC<StarRatingProps>` following the convention of CourseDetail and VideoPlayer
- Renders:
  - Full stars (&#9733; unicode) based on `Math.floor(average)`
  - A "half" star if `average - floor >= 0.5` (with reduced opacity)
  - Empty stars (&#9734; unicode) to complete up to 5
  - Informational text: "X.X (N)" or "No ratings (0)" if average is 0
- Imports styles from `./StarRating.module.scss`

**File to create:** `Frontend/src/components/StarRating/StarRating.module.scss`

**Description:**
- Import vars.scss explicitly (`@import '../../styles/vars.scss'`) following the convention of other existing SCSS modules
- Use `color('light-gray')` for empty stars
- Use `color('text-secondary')` for the info text
- Gold color `#fbbf24` for full and half stars (does not exist in the color system, used directly)
- Size variants `.sm` and `.md` that control `font-size` for stars and info
- Flex layout with gap for alignment

---

#### Task F2.2: Create RatingForm component (Client Component, interactive)

**File to create:** `Frontend/src/components/RatingForm/RatingForm.tsx`

**Description:**
- Create directory `Frontend/src/components/RatingForm/`
- MUST include `"use client"` as the first line (accesses localStorage, uses useState, handles events)
- Functional component with props: `courseSlug` (string), `onRatingSubmitted` (optional callback)
- Local state with `useState`:
  - `hoveredStar` (number): for hover effect
  - `selectedScore` (number): selected star
  - `comment` (string): textarea text
  - `isSubmitting` (boolean): loading state
  - `submitMessage` (string): feedback message
  - `submitError` (boolean): whether the submit failed
- Renders:
  - Title "Rate this course" (h3)
  - 5 interactive star buttons with hover effect and selection
  - Selected score indicator ("X/5")
  - Textarea for optional comment (placeholder, maxLength 1000, 3 rows)
  - Submit button with disabled/submitting states
  - Feedback message (green for success or red for error)
- `handleSubmit` handler:
  - Gets userId via `getUserId()` from `@/utils/userId`
  - POST to `http://localhost:8000/courses/${courseSlug}/ratings`
  - Body: `{ score, user_identifier, comment }` (comment is sent as `undefined` if empty, not as `""`)
  - Success and error handling with appropriate messages
- Accessibility: each star button has a descriptive `aria-label`

**File to create:** `Frontend/src/components/RatingForm/RatingForm.module.scss`

**Description:**
- Import vars.scss explicitly
- Container with `background: color('off-white')`, `border-radius: 18px`, `border: 2px solid color('light-gray')` (follows the section cards pattern)
- Star buttons: no border/background, cursor pointer, color and scale transition on hover, gold color `#fbbf24` when active
- Textarea: border `color('light-gray')`, focus with `color('primary')`, `border-radius: 12px`
- Submit button: `background: color('primary')`, `color: color('white')`, `border-radius: 12px`, hover with `translateY(-2px)` (same transition as `.backButton` in CourseDetail)
- Success message: green `#16a34a` with background `#f0fdf4`
- Error message: uses `color('primary')` as text with background `rgba(255, 45, 45, 0.05)`
- Disabled states with `opacity: 0.5` and `cursor: not-allowed`

---

#### Verification criteria F2

1. `yarn build` compiles without errors
2. The components can be imported without errors
3. Isolated visual verification (optional): create a temporary page that renders `<StarRating average={4.2} count={15} />` and `<RatingForm courseSlug="test" />` to validate styles and interactivity
4. The star hover in RatingForm works (color change on mouse over)
5. The form shows disabled states correctly when no score is selected

---

### Phase F3: Integration into Existing Components [COMPLETED]

**Status:** COMPLETED - StarRating integrated into Course and CourseDetail components, RatingForm added to CourseDetail, rating props passed from page.tsx.

**Objective:** Connect the new rating components into existing views (home and course detail).

**Dependencies:** Phase F2 completed. For full visual verification, the backend (Phases 1-3 of the architect's plan) must also be running and returning `average_rating` and `ratings_count` in the `/courses` and `/courses/{slug}` responses.

---

#### Task F3.1: Integrate StarRating into the Course component (home page card)

**File:** `Frontend/src/components/Course/Course.tsx`

**Changes:**
- Add import of `StarRating` from `@/components/StarRating/StarRating`
- Add `average_rating` and `ratings_count` to the props destructuring (already available via `Omit<CourseType, "slug">` after F1.1)
- Insert `<StarRating average={average_rating} count={ratings_count} size="sm" />` inside `.courseInfo`, between the teacher and the duration
- No changes needed in Course.module.scss for this basic integration (StarRating brings its own styles)

**Rationale:** Shows the average rating on each course card on the main page.

---

#### Task F3.2: Pass rating props on the Home page

**File:** `Frontend/src/app/page.tsx`

**Changes:**
- Add `average_rating={course.average_rating}` and `ratings_count={course.ratings_count}` to the `<CourseComponent>` JSX inside the `.map()` (current lines 34-39)
- No other changes needed (the fetch already returns Course[] and the type updated in F1.1 includes the new fields)

**Rationale:** Propagates rating data from the API response to the Course component that now needs it.

---

#### Task F3.3: Integrate StarRating and RatingForm into CourseDetail

**File:** `Frontend/src/components/CourseDetail/CourseDetail.tsx`

**Changes:**
- Add imports for `StarRating` and `RatingForm`
- Insert `<StarRating average={course.average_rating} count={course.ratings_count} size="md" />` inside `.courseInfo`, between the teacher and the description (after current line 31)
- Add a rating section at the end of the component (after `.classesSection`): a `<div className={styles.ratingSection}>` containing `<RatingForm courseSlug={course.slug} />`
- No need to modify the slug's `page.tsx` or pass additional props, since `course.slug` is available in the `course` prop that CourseDetailComponent receives

**File:** `Frontend/src/components/CourseDetail/CourseDetail.module.scss`

**Changes:**
- Add the `.ratingSection` class at the end of the file with `margin-top: 3rem` to visually separate the rating section from the class listing

**Rationale:** Shows the average rating alongside the course information and provides the form for users to rate.

---

#### Verification criteria F3

1. `yarn build` compiles without errors
2. `yarn dev` shows the home page with rating stars on each course card (values depend on the backend returning `average_rating` and `ratings_count`)
3. The course detail page shows stars in the header and the rating form at the bottom
4. The rating form allows selecting stars with a visual hover effect
5. If the backend is running: submitting a rating via the form returns "Rating submitted successfully" and the API receives the POST correctly
6. If the backend is running: reloading the course detail page shows the updated rating in the stars

---

### Phase F4: Test Updates [COMPLETED]

**Status:** COMPLETED - All 25 new/updated tests pass. Course test updated with rating fields, new tests created for StarRating (7), RatingForm (7), and userId (4).

**Objective:** Update existing tests that break due to the new fields and create tests for the new components.

**Dependencies:** Phases F1, F2, and F3 completed.

---

#### Task F4.1: Update existing Course test

**File:** `Frontend/src/components/Course/__test__/Course.test.tsx`

**Changes:**
- Add `average_rating: 4.5` and `ratings_count: 10` to the `mockCourse` object (current lines 8-13)
- Add a new test case `it("renders star rating")` that verifies the component renders rating information (look for the average and count text)
- Note: the test will look for the text rendered by StarRating. Since StarRating is a real component (not a mock), the test is a lightweight integration test. If isolation is preferred, StarRating can be mocked, but the current project convention is not to mock internal components (the Course test does not mock anything)

**Rationale:** The current mock data does not include `average_rating` or `ratings_count`, which will cause a TypeScript error (if strict) or render `undefined` in StarRating.

---

#### Task F4.2: Create test for StarRating

**File to create:** `Frontend/src/components/StarRating/__test__/StarRating.test.tsx`

**Description:**
- Follow the Course test convention (`__test__/` directory)
- Use `describe/it/expect` from Vitest and `render/screen` from `@testing-library/react`
- Tests to include:
  - Renders full stars based on the average (e.g., average=3 should show 3 full stars)
  - Renders "No ratings (0)" when average is 0 and count is 0
  - Renders the average with one decimal (e.g., "4.5 (10)")
  - Renders with size "sm" without errors
  - Renders 5 stars total (full + half + empty = 5)

---

#### Task F4.3: Create test for RatingForm

**File to create:** `Frontend/src/components/RatingForm/__test__/RatingForm.test.tsx`

**Description:**
- Follow the `__test__/` directory convention
- Requires a global `fetch` mock (pattern already used in `page.test.tsx` for classes)
- Requires a `localStorage` mock (jsdom provides it, but may need setup)
- Requires a `crypto.randomUUID` mock if not available in jsdom
- Tests to include:
  - Renders the title "Rate this course"
  - Renders 5 star buttons
  - The submit button is initially disabled (score = 0)
  - Clicking a star selects the score and enables the submit button
  - Renders the comment textarea
  - On successful submit, shows a success message
  - On submit with network error, shows an error message

**Rationale:** It is a Client Component with complex logic (state, fetch, localStorage) that deserves test coverage.

---

#### Task F4.4: Create test for userId utility

**File to create:** `Frontend/src/utils/__test__/userId.test.ts`

**Description:**
- Pure unit test (no React)
- Tests to include:
  - Returns an empty string when `window` is not defined (simulate SSR)
  - Generates and persists a UUID in localStorage
  - Returns the same UUID on subsequent calls
  - Uses the key `platziflix_user_id` in localStorage

---

#### Verification criteria F4

1. `yarn test` passes all tests (new and existing)
2. No TypeScript warnings in test files
3. Tests cover the critical paths: rendering, star interaction, successful submit, submit with error, userId generation

---

## File summary by phase

### Phase F1: Types and Utilities
| Action | File |
|--------|---------|
| Modify | `Frontend/src/types/index.ts` |
| Create | `Frontend/src/utils/userId.ts` |

### Phase F2: New Components
| Action | File |
|--------|---------|
| Create | `Frontend/src/components/StarRating/StarRating.tsx` |
| Create | `Frontend/src/components/StarRating/StarRating.module.scss` |
| Create | `Frontend/src/components/RatingForm/RatingForm.tsx` |
| Create | `Frontend/src/components/RatingForm/RatingForm.module.scss` |

### Phase F3: Integration
| Action | File |
|--------|---------|
| Modify | `Frontend/src/components/Course/Course.tsx` |
| Modify | `Frontend/src/app/page.tsx` |
| Modify | `Frontend/src/components/CourseDetail/CourseDetail.tsx` |
| Modify | `Frontend/src/components/CourseDetail/CourseDetail.module.scss` |

### Phase F4: Tests
| Action | File |
|--------|---------|
| Modify | `Frontend/src/components/Course/__test__/Course.test.tsx` |
| Create | `Frontend/src/components/StarRating/__test__/StarRating.test.tsx` |
| Create | `Frontend/src/components/RatingForm/__test__/RatingForm.test.tsx` |
| Create | `Frontend/src/utils/__test__/userId.test.ts` |

**Totals:** 5 new code files + 3 new test files + 5 modified files (1 existing test + 4 production) = **8 new files, 5 modified files**.

---

## Dependency diagram

```
Phase F1 (Types + userId utility)
  |
  v
Phase F2 (StarRating + RatingForm components)
  |
  v
Phase F3 (Integration into Course, CourseDetail, page.tsx)
  |
  v
Phase F4 (New tests + existing test update)

--- External dependency ---
Backend Phases 1-3 must be complete for visual verification of F3
Backend Phase 3 must be complete for functional verification of F3 (POST rating)
```

---

## Additional technical notes

### On the auto-import of vars.scss

The current `next.config.ts` has `prependData: '@import "vars.scss"'`, which injects vars.scss at the beginning of every SCSS file. However, all existing `.module.scss` files also have an explicit import `@import '../../styles/vars.scss'`. This is redundant but does not cause errors (SCSS tolerates duplicate imports of the same file). New files must follow the same convention: include the explicit import for consistency with the rest of the codebase.

### On the onRatingSubmitted callback

The architect includes a prop `onRatingSubmitted?: () => void` in RatingForm. This callback is not used in the current integration (CourseDetailComponent does not pass this prop). Its purpose would be to refresh the rating data after a successful submit. However, given that:
- CourseDetailComponent is a Server Component
- Data is fetched on the server via `cache: "no-store"`
- There is no client-side revalidation mechanism without router.refresh()

For the updated rating to be reflected immediately after submission, it would require:
1. Calling `router.refresh()` from the Client Component (requires access to the Next.js router)
2. Or telling the user to reload the page
3. Or implementing optimistic local state

The simplest implementation for the first version is to leave the callback unused and rely on `cache: "no-store"` so that reloading the page shows the updated data. The prop is kept for future extensibility.

### On testing Server Components

The existing `page.test.tsx` (classes) test uses `renderToString` from `react-dom/server` to test async Server Components. The StarRating tests can use the normal `render` from RTL since StarRating is not async (it does not fetch). If full page integration testing were desired, the `renderToString` pattern with fetch mocks would be used.
