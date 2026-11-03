# Student Management System

Full-stack, role-based (Admin / Faculty / Student) app.
**React (Vite) → FastAPI → Neon PostgreSQL.** Hosting: Vercel (frontend), Render (backend), Neon (database).

```
student-management-system/
├── backend/   FastAPI + SQLAlchemy + Alembic (app/, alembic/, seed.py, tests/)
└── frontend/  React + React Router + Axios (src/...)
```

## 1. Run it on Windows (VS Code)

Install: Python 3.11+ (tick "Add to PATH"), Node.js LTS, Git, VS Code. Open this folder in VS Code
(File → Open Folder), then Terminal → New Terminal.

### A. Create the Neon database
1. Sign up at https://neon.tech → Create project → copy the **connection string** (Connect button).
   It looks like `postgresql://user:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require`.

### B. Backend
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
copy .env.example .env
```
Edit `backend\.env`: paste your Neon string into `DATABASE_URL`, and generate a secret:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
Paste that into `SECRET_KEY`. Then create the tables and the first admin:
```powershell
alembic upgrade head
python seed.py --email admin@example.com --password "ChangeMe#12345" --demo
uvicorn app.main:app --reload
```
(`--demo` adds a sample department/course/faculty/student; leave it off for a clean database.)
Open http://localhost:8000/docs (Swagger). Click **POST /auth/login → Try it out**, log in, copy the
`access_token`, click **Authorize** (top right), paste it. You can now call protected endpoints.

Demo logins (only with `--demo`): `faculty@example.com / Faculty#123`, `student@example.com / Student#123`.

### C. Frontend (second terminal)
```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```
Open http://localhost:5173 and log in. Pick the matching tab (Admin / Faculty / Student).

### D. Automated backend check (optional, uses a temporary SQLite file, never touches Neon)
```powershell
cd backend
python -m tests.smoke_test
```
Expected: `42/42 checks passed`.

## 2. Suggested first walkthrough
1. Admin: Departments → Courses → Subjects → Faculty (assign courses) → Students.
2. Faculty (another browser/device): Attendance → pick course/subject/date → Save. Marks → New examination → enter marks.
3. Student (phone): Dashboard / Attendance / Marks update immediately because all use the same Neon database.
4. Admin: Dashboard numbers change; Reports → download CSV (opens in Excel).

## 3. Database relationships
- `users` (email, password_hash, role, is_active) — one login record per person.
- `students.user_id` and `faculty.user_id` → `users.id` (1:1, unique). Deleting the user deletes the profile.
- `departments` 1─N `courses` 1─N `subjects`. Students and faculty belong to a department; students have a primary course.
- `enrollments` = students M:N courses (unique student+course).
- `faculty_courses` = faculty M:N courses (unique faculty+course). This table drives faculty permissions.
- `attendance` → student, course, subject, faculty. **Unique (student, subject, date)** prevents duplicates.
- `examinations` → course, subject (with `max_marks`). `marks` → student, examination; **unique (student, exam)**,
  `version` column for optimistic locking.
- Departments/courses that are still in use cannot be deleted (foreign keys return HTTP 409).

## 4. Security design
- Passwords hashed with **Argon2**. JWT (HS256) with expiry (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- The role is always read from the **database**, never from the request. The login-page role tab only checks that you used the right portal.
- Admin creates all accounts. There is no public registration.
- Deactivated users are rejected on every request, so existing tokens stop working immediately.
- **IDOR**: student endpoints take no ID in the URL; they use the logged-in student's own record.
  Faculty endpoints verify the course is assigned to the faculty (`assert_course_access`); unknown/unassigned records return 403/404.
- Student profile updates accept only phone and address (Pydantic schema ignores everything else).
- CORS allows only origins in `CORS_ORIGINS`. Token is kept in `sessionStorage` (cleared on tab close/logout).
  Trade-off: any XSS could read it; the app renders no raw HTML, which mitigates this. HTTPS is enforced by Render/Vercel.
- Concurrency: unique constraints + transactions for attendance; optimistic locking (`version`) for marks; HTTP 409 on conflicts.

## 5. API summary (full docs at /docs)
| Area | Endpoints |
|---|---|
| Auth | `POST /auth/login`, `GET /auth/me`, `POST /auth/change-password` |
| Admin | `/admin/students` (CRUD, search, filter, pagination), `/admin/faculty` (CRUD + `/{id}/courses`), `/admin/enrollments`, `GET /admin/dashboard`, `GET /admin/reports/{students\|attendance\|performance}` |
| Setup | `/departments`, `/courses`, `/subjects` (read: any logged-in user, write: admin) |
| Faculty | `GET /faculty/dashboard`, `/courses`, `/students`, `POST/GET /faculty/attendance`, `GET /faculty/attendance/summary`, `/faculty/examinations`, `POST/GET /faculty/marks`, `PUT /faculty/marks/{id}` |
| Student | `GET /student/dashboard`, `GET/PUT /student/profile`, `/attendance`, `/marks`, `/courses` |

Grades: ≥90 A+, ≥80 A, ≥70 B+, ≥60 B, ≥50 C, ≥40 D, else F (edit `grade_for` in `backend/app/services/common.py`).

## 6. Deployment (recommended: everything on ONE Vercel project)

The repo root contains `vercel.json`, `requirements.txt`, `.python-version` and `api/index.py`.
Vercel builds the React app (static) and runs the FastAPI backend as a serverless function under `/api`,
on the same domain, so there is no CORS setup.

1. **Create the database tables from your PC first** (Vercel does not run migrations):
   `cd backend` -> `alembic upgrade head` -> `python seed.py --email ... --password ...`
2. **GitHub**: create an empty repo, then from the project root:
   `git init`, `git add .`, `git status` (confirm `.env` is NOT listed), `git commit -m "Initial commit"`,
   `git branch -M main`, `git remote add origin <repo-url>`, `git push -u origin main`.
3. **Vercel**: Add New -> Project -> import the repo. Keep **Root Directory = repository root** (not `frontend`).
   Leave build settings as detected (they come from `vercel.json`). Add Environment Variables:
   - `DATABASE_URL` = `postgresql+psycopg://USER:PASSWORD@HOST-pooler.../neondb?sslmode=require` (the Neon pooled string)
   - `SECRET_KEY` = a long random string
   Then Deploy.
4. Open `https://YOUR-APP.vercel.app` (the app) and `https://YOUR-APP.vercel.app/api/docs` (Swagger).
5. After changing environment variables in Vercel, redeploy for them to take effect.

Notes: serverless functions wake up on demand, so the first request can be a little slower. Database changes
(new models) still need `alembic upgrade head` run from your PC against Neon.

### Alternative: separate hosting (Render for backend + Vercel for frontend)
- Render: Root Directory `backend`; Build `pip install -r requirements.txt`;
  Start `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`;
  env vars `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS=https://YOUR-APP.vercel.app`.
- Vercel: Root Directory `frontend`, env `VITE_API_URL=https://YOUR-API.onrender.com`.
  (If you do this, delete the root `vercel.json` and `api/` folder.)

## 7. Final test checklist
- [ ] Admin, Faculty, Student can each log in; wrong portal tab or password is rejected
- [ ] Student/faculty cannot open `/admin/...` pages (redirected) or call admin APIs (403 in Swagger)
- [ ] Admin adds a student → Faculty sees them in the course → attendance → Student sees it on a phone
- [ ] Faculty enters marks → Student sees result and grade → Admin dashboard updates
- [ ] Deactivating an account blocks login immediately
- [ ] Duplicate student ID / email shows a clear error
- [ ] Layout works at phone width (sidebar becomes a ☰ menu)

## 8. Troubleshooting
- `ModuleNotFoundError: app` → run commands from inside `backend/` with the venv active.
- `could not connect to server` / SSL errors → re-copy the Neon string; keep `?sslmode=require`; if you see a `channel_binding` problem, delete `&channel_binding=require`.
- Browser "CORS error" → `CORS_ORIGINS` must exactly match the frontend URL (no trailing slash).
- Frontend shows network errors → check `VITE_API_URL`, then restart `npm run dev` (env is read at start/build).
- New models later: `alembic revision --autogenerate -m "message"` then `alembic upgrade head`.
