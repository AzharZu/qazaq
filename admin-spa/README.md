# Admin SPA (React + TypeScript + shadcn-style UI)

Full-featured admin panel for Qazaq Platform with CRUD for courses, modules, lessons, blocks, vocabulary, placement, and read-only users. Auth is cookie-based against `/api/auth/login` (session cookie), with `/api/auth/me` used for role checks.

## Tech
- React 18 + TypeScript
- Vite
- Tailwind + lightweight shadcn-style components (Radix Dialog/Toast)
- Axios (withCredentials)

## Scripts
- `npm install`
- `npm run dev` (default port 5174)
- `npm run build`
- `npm run preview`

## Backend expectations
- Backend running at the same origin with routes:
  - `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`
  - `/api/courses`, `/api/modules`, `/api/lessons`, `/api/blocks`, `/api/vocabulary`
  - `/api/placement/admin`
  - `/api/users`

## Routes
- `/admin/login`
- `/admin/dashboard`
- `/admin/courses`
- `/admin/modules/:id`
- `/admin/lessons/:id`
- `/admin/blocks/:id`
- `/admin/vocabulary`
- `/admin/placement`
- `/admin/users`

## How to test CRUD
1. Start backend (`uvicorn app.main:app --reload`) with session cookies enabled.
2. From `admin-spa/`:
   ```bash
   npm install
   npm run dev
   ```
3. Visit `/admin/login`, sign in with an admin user.
4. Navigate to each section:
   - Courses/Modules/Lessons/Blocks/Vocabulary: create, edit, delete using the forms and confirmation modals.
   - Placement: manage questions (answers field expects JSON).
   - Users: view list (read-only).
5. Verify requests hit `/api/*` and cookies are sent (`withCredentials` enabled in axios).
